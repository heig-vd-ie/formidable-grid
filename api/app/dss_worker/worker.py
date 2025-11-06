from datetime import datetime
import json
import os
import random
import time

import numpy as np
import pandas as pd

from app.common.konfig import *
from app.common.models import ExtraUnitRequest, InputDSSWorker, ProfileData
from app.common.setup_log import setup_logger
from app.helpers import clean_nans, setup_env_vars
import ray

logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(
        self,
        input_dss_worker: InputDSSWorker,
        profiles: ProfileData,
        extra_unit_request: ExtraUnitRequest,
    ):
        from opendssdirect import dss

        self.dss = dss
        self.input_dss_worker = input_dss_worker
        self.profiles = profiles
        self.extra_unit_request = extra_unit_request

        self._initialize_worker_dirs()
        self._setup_circuit()

    def _initialize_worker_dirs(self):
        """Initialize working directories & env vars"""
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        setup_env_vars(self.input_dss_worker.env_vars)
        os.chdir(self.input_dss_worker.basedir)

    def _setup_circuit(self):
        """Set up circuit in opendss"""
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{self.input_dss_worker.temp_file}"')
        self.buses = self.dss.Circuit.AllBusNames() or []

        """Add extra PV systems and storage units to the circuit for testing"""
        for i in range(self.extra_unit_request.number_of_pvs):
            seed = self.extra_unit_request.seed_number + i + 1
            random.seed(seed)
            np.random.seed(seed)

            bus_name = random.choice(self.buses)
            pv_shape = f"pvshape{(i % 5) + 1}"

            self.dss.Command(
                f'New "PVSystem.PV{i+1}" Phases=3 conn=delta Bus1={bus_name} %Cutin=0 %Cutout=0 '
                f"kV=4.16 pmpp={self.extra_unit_request.pv_kva} daily={pv_shape} "
                f"kVA={self.extra_unit_request.pv_kva * 1.1} %X=50 kP=0.3 KVDC=0.700 PITol=0.1"
            )

            if random.random() < self.extra_unit_request.gfmi_percentage:
                self.dss.Command(
                    f'New "Storage.Storage{i+1}" Phases=3 conn=wye Bus1={bus_name} '
                    f"kV=4.16 kWrated={self.extra_unit_request.storage_kva} "
                    f"kWhrated={self.extra_unit_request.storage_kva * 4000}"
                )

        self.storage_kva = self.extra_unit_request.storage_kva

        """Cache circuit components for faster access"""
        self.loads = [l for l in self.dss.Loads.AllNames() or [] if "Storage" not in l]
        self.lines = self.dss.Lines.AllNames() or []
        self.transformers = self.dss.Transformers.AllNames() or []
        self.generators = [
            g for g in self.dss.Generators.AllNames() or [] if "Storage" not in g
        ]
        self.storages = self.dss.Storages.AllNames() or []
        self.pvsystems = self.dss.PVsystems.AllNames() or []
        self.loadshapes = [
            l for l in self.dss.LoadShape.AllNames() or [] if "loadshape" in l
        ]
        self.pvloadshapes = [
            l for l in self.dss.LoadShape.AllNames() or [] if "pvshape" in l
        ]
        self.vsources = [
            v for v in self.dss.Vsources.AllNames() or [] if "fictive" in v
        ]

    def solve(self, curr_datetime: datetime):
        """Run power flow for a single timestep"""
        import logging
        import sys

        start = time.time()
        self._set_load_shape_multipliers(curr_datetime)
        self.dss.run_command("Solve")
        freqs = [NOMINAL_FREQUENCY]
        Δp, Δq = self._extract_load_n_pv_powers()

        for _ in range(MAX_ITERATION):
            self._set_power_storages(Δp, Δq)
            self.dss.run_command("Solve")
            freqs.append(self._update_freq(Δp))
            if abs(freqs[-1] - freqs[-2]) / NOMINAL_FREQUENCY < SMALL_NUMBER:
                break

        self._dump_results(time.time() - start, curr_datetime, freqs)
        sys.stdout.flush()
        sys.stderr.flush()
        logging.shutdown()
        return None

    def _set_load_shape_multipliers(self, curr_datetime: datetime):
        """Set load and PV shape multipliers based on profiles"""

        def __set_shapes(shapes: list, profile_data: pd.DataFrame):
            for i, shape in enumerate(shapes):
                col = profile_data.columns[i % len(profile_data.columns)]
                multiplier = profile_data.iloc[0][col]
                self.dss.run_command(
                    f"Edit LoadShape.{shape} npts=1 mult=[{multiplier}]"
                )

        pv = self.profiles.pv[self.profiles.pv.index == curr_datetime]
        load_p = self.profiles.load_p[self.profiles.load_p.index == curr_datetime]
        load_q = self.profiles.load_q[self.profiles.load_q.index == curr_datetime]

        if pv.empty or load_p.empty or load_q.empty:
            logger.warning(f"No profile data for {curr_datetime}")
            return

        __set_shapes(self.loadshapes, load_p)
        __set_shapes(self.pvloadshapes, pv)

    def _extract_load_n_pv_powers(self):
        """Sum powers of loads and PV systems"""

        def __extract_power(powers, Δp, Δq):
            return Δp + sum(powers[::2]), Δq + sum(powers[1::2])

        Δp = Δq = 0.0
        for name, elements in [("Load", self.loads), ("PVSystem", self.pvsystems)]:
            for el in elements:
                self.dss.Circuit.SetActiveElement(f"{name}.{el}")
                Δp, Δq = __extract_power(self.dss.CktElement.Powers(), Δp, Δq)
        return Δp, Δq

    def _update_freq(self, Δp: float):
        """Frequency update based on droop and storage capacity"""
        Δf = (
            -Δp
            * NOMINAL_FREQUENCY
            * NOMINAL_DROOP
            / (len(self.storages) * self.storage_kva)
        )
        return NOMINAL_FREQUENCY + Δf

    def _set_power_storages(self, Δp: float, Δq: float):
        for storage in self.storages:
            self.dss.Circuit.SetActiveElement(f"Storage.{storage}")
            set_point = Δp * 3 / len(self.storages)
            self.dss.run_command(f"Edit Storage.{storage} kW={set_point}")

    def _dump_results(
        self,
        delta_time: float,
        curr_datetime: datetime,
        freqs: list[float],
    ):
        timestamp = curr_datetime.strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": curr_datetime.isoformat(),
            "solve_time_ms": delta_time,
            "converged": bool(self.dss.Solution.Converged()),
            "frequency": freqs[-1],
            "frequencies": freqs,
            "losses": self.dss.Circuit.Losses(),
            "voltages": {bus: self.dss.Bus.Voltages() for bus in self.buses},
            "lines": self.__get_dict_data("line"),
            "loads": self.__get_dict_data("load"),
            "generators": self.__get_dict_data("generator"),
            "storages": self.__get_dict_data("storage"),
            "pvsystems": self.__get_dict_data("pvsystem"),
            "vsources": self.__get_dict_data("vsource"),
        }
        cleaned = clean_nans(results)
        with open(os.path.join(OUTPUT_FOLDER, f"results_{timestamp}.json"), "w") as f:
            json.dump(cleaned, f, indent=4)

    def __get_dict_data(self, klass: str) -> dict:
        elements = getattr(self, f"{klass}s")
        results = {}
        for el in elements:
            self.dss.Circuit.SetActiveElement(f"{klass}.{el}")
            results[f"{klass}.{el}"] = {
                "bus_names": self.dss.CktElement.BusNames(),
                "powers": self.dss.CktElement.Powers(),
                "voltages": self.dss.CktElement.Voltages(),
                "currents": self.dss.CktElement.Currents(),
            }
        return results
