from datetime import datetime
import json
import os
import random
import time
import numpy as np
import pandas as pd
from konfig import *
from data_model import (
    FreqCoefficients,
    GfmKace,
    ElementsSetPoints,
    ProfileData,
    SetPoints,
)
from opendss_indirect.power_flow import update_freq
from setup_log import setup_logger
from helpers import clean_nans, initialize_dirs, threephase_tuple_to_pq
import ray

logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(
        self,
        temp_filepath: str,
        profiles: ProfileData,
        gfm_kace: GfmKace,
    ):
        from opendssdirect import dss

        self.dss = dss
        self.temp_filepath = temp_filepath
        self.profiles = profiles
        self.gfm_kace = gfm_kace

        initialize_dirs()
        self._setup_circuit()

    def _setup_circuit(self):
        """Set up circuit in opendss"""
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{self.temp_filepath}"')
        self.buses = self.dss.Circuit.AllBusNames() or []

        """Add extra PV systems and storage units to the circuit for testing"""
        for i in range(self.gfm_kace.number_of_pvs):
            seed = self.gfm_kace.seed_number + i + 1
            random.seed(seed)
            np.random.seed(seed)

            bus_name = random.choice(self.buses)
            pv_shape = f"pvshape{(i % NUMBER_OF_PV_SHAPES) + 1}"

            self.dss.Command(
                f'New "PVSystem.PV{i+1}" Phases=3 conn=delta Bus1={bus_name} %Cutin=0 %Cutout=0 '
                f"kV=4.16 pmpp={self.gfm_kace.pv_kva} daily={pv_shape} "
                f"kVA={self.gfm_kace.pv_kva * 1.1} %X=50 kP=0.3 KVDC=0.700 PITol=0.1"
            )

            if random.random() < self.gfm_kace.gfmi_percentage:
                self.dss.Command(
                    f'New "Storage.Storage{i+1}" Phases=3 conn=wye Bus1={bus_name} '
                    f"kV=4.16 kWrated={self.gfm_kace.storage_kva} "
                    f"kWhrated={self.gfm_kace.storage_kva * 4000}"
                )

        self.storage_kva = self.gfm_kace.storage_kva

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
        self.freq_coeff = FreqCoefficients(
            damping=NOMINAL_DAMPING,
            droop={name: NOMINAL_DROOP for name in self.storages},
        )

    def solve(self, curr_datetime: datetime):
        """Run power flow for a single timestep"""
        import logging
        import sys

        start = time.time()
        self._set_load_shape_multipliers(curr_datetime)
        self.dss.run_command("Solve")
        freqs = [NOMINAL_FREQUENCY]
        el_sps = self._extract_powers()

        for _ in range(MAX_ITERATION):
            freq = update_freq(el_sps=el_sps, freq_coeff=self.freq_coeff)
            freqs.append(freq)
            self._set_power_storages(freq=freq, el_sps=el_sps)
            self.dss.run_command("Solve")
            if abs(freqs[-1] - freqs[-2]) / NOMINAL_FREQUENCY < SMALL_NUMBER:
                break

        self._dump_results(time.time() - start, curr_datetime, freqs)
        sys.stdout.flush()
        sys.stderr.flush()
        logging.shutdown()
        return None

    def _set_load_shape_multipliers(self, curr_datetime: datetime):
        """Set load and PV shape multipliers based on profiles"""

        pv = self.profiles.pv[self.profiles.pv.index == curr_datetime]
        load_p = self.profiles.load_p[self.profiles.load_p.index == curr_datetime]
        load_q = self.profiles.load_q[self.profiles.load_q.index == curr_datetime]

        if pv.empty or load_p.empty or load_q.empty:
            logger.warning(f"No profile data for {curr_datetime}")
            return

        self.__set_shapes(self.loadshapes, load_p)
        self.__set_shapes(self.pvloadshapes, pv)

    def __set_shapes(self, shapes: list, profile_data: pd.DataFrame):
        for i, shape in enumerate(shapes):
            col = profile_data.columns[i % len(profile_data.columns)]
            multiplier = profile_data.iloc[0][col]
            self.dss.run_command(f"Edit LoadShape.{shape} npts=1 mult=[{multiplier}]")

    def _extract_powers(self) -> ElementsSetPoints:
        """Sum powers of loads and PV systems"""
        setpoints = {}
        for name, elements in [
            ("Load", self.loads),
            ("PVSystem", self.pvsystems),
            ("Storage", self.storages),
        ]:
            p = q = {}
            for el in elements:
                self.dss.Circuit.SetActiveElement(f"{name}.{el}")
                p[f"{name}.{el}"], q[f"{name}.{el}"] = threephase_tuple_to_pq(
                    self.dss.CktElement.Powers()
                )
            setpoints[name] = SetPoints(p=p, q=q)
        return ElementsSetPoints(
            load=setpoints["Load"],
            pvsystem=setpoints["PVSystem"],
            storage=setpoints["Storage"],
        )

    def _set_power_storages(self, freq: float, el_sps: ElementsSetPoints):
        for storage in self.storages:
            self.dss.Circuit.SetActiveElement(f"Storage.{storage}")
            set_point = (freq - NOMINAL_FREQUENCY) * self.freq_coeff.droop[
                storage
            ] + el_sps.storage.p[storage]
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
