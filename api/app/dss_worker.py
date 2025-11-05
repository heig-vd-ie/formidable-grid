from datetime import datetime, timedelta
import json
import os
import random
import time

import numpy as np
import psutil
import ray
from tqdm import tqdm

from extract_data.profile_reader import ProfileData, ProfileReader
from app.helpers import clean_nans, remove_json_files, setup_circuit, setup_env_vars
from app.models import ExtraUnitRequest, InputDSSWorker
from common.konfig import *
from common.setup_log import setup_logger

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

        self._setup()

    def _setup(self):
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        remove_json_files()
        setup_env_vars(self.input_dss_worker.env_vars)
        os.chdir(self.input_dss_worker.basedir)
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{self.input_dss_worker.temp_file}"')
        self.buses = self.dss.Circuit.AllBusNames() or []

        self._add_extra_units()
        self._initialize_component_cache()

    def _add_extra_units(self):
        """Add extra PV systems and storage units to the circuit for testing"""
        for i in range(self.extra_unit_request.number_of_pvs):
            seed = self.extra_unit_request.seed_number + i + 1
            random.seed(seed)
            np.random.seed(seed)

            bus_name = random.choice(self.buses)
            pv_shape = f"pvshape{(i % 5) + 1}"

            self.dss.Command(
                f'New "PVSystem.PV{i+1}" Phases=3 conn=delta Bus1={bus_name} '
                f"kV=4.16 pmpp=100 daily={pv_shape} kVA={self.extra_unit_request.pv_kva} "
                f"%X=50 kP=0.3 KVDC=0.700 PITol=0.1"
            )

            if random.random() < self.extra_unit_request.gfmi_percentage:
                self.dss.Command(
                    f'New "Storage.Storage{i+1}" Phases=3 conn=wye Bus1={bus_name} '
                    f"kV=4.16 kWrated={self.extra_unit_request.storage_kva} "
                    f"kWhrated={self.extra_unit_request.storage_kva * 4000}"
                )

        self.storage_kva = self.extra_unit_request.storage_kva

    def _initialize_component_cache(self):
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
        start = time.time()
        self._set_load_shape_multipliers(curr_datetime)
        self.dss.run_command("Solve")

        Δp, Δq = self._extract_load_pv_powers()
        freqs = [NOMINAL_FREQUENCY]
        freq = NOMINAL_FREQUENCY

        for _ in range(MAX_ITERATION):
            freq = self._update_freq(freq, Δp)
            self._set_power_storages(Δp, Δq)
            self.dss.run_command("Solve")
            freqs.append(freq)
            if abs(freq - freqs[-2]) / NOMINAL_FREQUENCY < SMALL_NUMBER:
                break

        self._dump_results(time.time() - start, curr_datetime, freq, freqs)
        return None

    def _set_load_shape_multipliers(self, curr_datetime: datetime):
        """Set load and PV shape multipliers based on profiles"""

        def set_shapes(shapes, profile_data):
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

        set_shapes(self.loadshapes, load_p)
        set_shapes(self.pvloadshapes, pv)

    def _extract_load_pv_powers(self):
        """Sum powers of loads and PV systems"""
        Δp = Δq = 0.0
        for name, elements in [("Load", self.loads), ("PVSystem", self.pvsystems)]:
            for el in elements:
                self.dss.Circuit.SetActiveElement(f"{name}.{el}")
                dp, dq = self.__extract_power(self.dss.CktElement.Powers())
                Δp += dp
                Δq += dq
        return Δp, Δq

    @staticmethod
    def __extract_power(powers):
        return sum(powers[::2]), sum(powers[1::2])

    def _update_freq(self, freq: float, Δp: float):
        """Frequency update based on droop and storage capacity"""
        Δf = (
            -Δp
            * NOMINAL_FREQUENCY
            * NOMINAL_DROOP
            / (len(self.storages) * self.storage_kva)
        )
        return freq + Δf

    def _set_power_storages(self, Δp: float, Δq: float):
        for storage in self.storages:
            self.dss.Circuit.SetActiveElement(f"Storage.{storage}")
            mult_p = Δp * 3 / (self.storage_kva * len(self.storages))
            self.dss.run_command(
                f"Edit LoadShape.{storage}Shape npts=1 mult=[{mult_p}]"
            )

    def _dump_results(
        self,
        delta_time: float,
        curr_datetime: datetime,
        freq: float,
        freqs: list[float],
    ):
        timestamp = curr_datetime.strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": curr_datetime.isoformat(),
            "solve_time_ms": delta_time,
            "converged": bool(self.dss.Solution.Converged()),
            "frequency": freq,
            "frequencies": freqs,
            "losses": self.dss.Circuit.Losses(),
            "voltages": self.__get_voltages(),
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

    def __get_voltages(self) -> dict:
        return {bus: self.dss.Bus.Voltages() for bus in self.buses}


def run_daily_powerflow(
    extra_unit_request: ExtraUnitRequest = ExtraUnitRequest(),
    dss_filename: str = "Run_QSTS.dss",
    from_datetime: datetime = datetime(2025, 1, 1),
    to_datetime: datetime = datetime(2025, 1, 2),
):

    cpu_count = psutil.cpu_count() or MAX_CPU_COUNT
    logger.info(f"{cpu_count} CPU cores available")

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit(dss_filename)
    profiles = ProfileReader().process_and_record_profiles().get_profiles()

    total_runs = int((to_datetime - from_datetime).total_seconds() // (60 * 15))
    logger.info(f"Total runs: {total_runs}")
    run_iter = iter(range(total_runs))

    workers = [
        DSSWorker.remote(
            InputDSSWorker(basedir, temp_file, env_vars), profiles, extra_unit_request
        )
        for _ in range(cpu_count - 1)
    ]

    futures = []
    # assign first batch
    for worker in workers:
        try:
            run_idx = next(run_iter)
            futures.append(
                (
                    worker,
                    worker.solve.remote(
                        from_datetime + timedelta(minutes=run_idx * 15)
                    ),
                )
            )
        except StopIteration:
            break

    pbar = tqdm(total=total_runs, desc="Running Power Flows")
    while futures:
        done_ids, _ = ray.wait([f[1] for f in futures])
        done_id = done_ids[0]
        for i, (worker, future) in enumerate(futures):
            if future == done_id:
                try:
                    ray.get(done_id)
                except Exception as e:
                    logger.error(f"Error in worker id {done_id}: {e}")
                    ray.cancel(done_id)
                pbar.update(1)
                try:
                    run_idx = next(run_iter)
                    futures[i] = (
                        worker,
                        worker.solve.remote(
                            from_datetime + timedelta(minutes=run_idx * 15)
                        ),
                    )
                except StopIteration:
                    futures.pop(i)
                break
    pbar.close()
    os.remove(temp_file)
