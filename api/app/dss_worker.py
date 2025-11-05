from datetime import datetime, timedelta
import json
import os
import random
import shutil
import time

import numpy as np
import psutil
import ray
from tqdm import tqdm

from extract_data.profile_reader import ProfileData, ProfileReader
from app.helpers import clean_nans, setup_circuit
from app.models import RunDailyExampleRequest, InputDSSWorker
from common.konfig import *
from common.setup_log import setup_logger


logger = setup_logger(__name__)


@ray.remote
class DSSWorker:
    def __init__(
        self,
        input_dss_worker: InputDSSWorker,
        profiles: ProfileData,
        extra_unit_request: RunDailyExampleRequest,
    ):
        from opendssdirect import dss

        self.input_dss_worker = input_dss_worker
        self.dss = dss
        self.profiles = profiles
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        self._remove_json_files()
        self.__init_dir(input_dss_worker.env_vars)
        os.chdir(self.input_dss_worker.basedir)
        self.dss.Command("Clear")
        self.dss.Command(f'Compile "{input_dss_worker.temp_file.__str__()}"')
        self.buses = self.dss.Circuit.AllBusNames() or []
        self._add_extra_units(extra_unit_request=extra_unit_request)
        self.__init_components()

    def __init_dir(self, env_vars: dict):
        for key, value in env_vars.items():
            os.environ[key] = value

    def _remove_json_files(self):
        """Remove all JSON files from the output directory"""
        for filename in os.listdir(OUTPUT_FOLDER):
            file_path = os.path.join(OUTPUT_FOLDER, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}. Reason: {e}")

    def __init_components(self):
        """Initialize component lists from the OpenDSS circuit"""
        self.loads = [l for l in self.dss.Loads.AllNames() or [] if not "Storage" in l]
        self.lines = self.dss.Lines.AllNames() or []
        self.transformers = self.dss.Transformers.AllNames() or []
        self.generators = [
            g for g in self.dss.Generators.AllNames() or [] if not "Storage" in g
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

    def _add_extra_units(self, extra_unit_request: RunDailyExampleRequest):
        """Add extra PV systems and storage units to the circuit for testing"""
        for i in range(extra_unit_request.number_of_pvs):
            random.seed(seed_number := extra_unit_request.seed_number + 1)
            np.random.seed(seed_number)
            bus_name = random.choice(self.buses)
            pv_shape = "pvshape" + str((i % 5) + 1)  # Cycle through pvshape1-5
            self.dss.Command(
                f'New "PVSystem.PV{i+1}" Phases=3 conn=delta '
                f"Bus1={bus_name} kV=4.16 pmpp=100 "
                f"daily={pv_shape} kVA={extra_unit_request.pv_kva} "
                f"%X=50 kP=0.3 KVDC=0.700 PITol=0.1"
            )
            if (
                random.random() < extra_unit_request.gfmi_percentage
            ):  # is it grid-forming?
                self.dss.Command(
                    f'New "Storage.Storage{i+1}" Phases=3 conn=wye '
                    f"Bus1={bus_name} kV=4.16 kWrated={extra_unit_request.storage_kva} "
                    f"kWhrated={extra_unit_request.storage_kva*4000}"
                )
        self.storage_kva = extra_unit_request.storage_kva
        self.__init_components()

    def _set_load_shape_multipliers(self, curr_datetime: datetime):
        """Randomly set load shape multipliers for all load shapes"""
        pv = abs(self.profiles.pv[self.profiles.pv.index == curr_datetime])
        load_p = abs(self.profiles.load_p[self.profiles.load_p.index == curr_datetime])
        load_q = abs(self.profiles.load_q[self.profiles.load_q.index == curr_datetime])
        if pv.empty or load_p.empty or load_q.empty:
            logger.warning(f"No profile data found for {curr_datetime}")
            return
        for i in range(len(self.loadshapes)):
            col_name = load_p.columns[i % len(load_p.columns)]
            multiplier = load_p.iloc[0][col_name]
            self.dss.run_command(
                f"Edit LoadShape.{self.loadshapes[i]} npts=1 mult=[{multiplier}]"
            )
        for i in range(len(self.pvloadshapes)):
            col_name = pv.columns[i % len(pv.columns)]
            multiplier = pv.iloc[0][col_name]
            self.dss.run_command(
                f"Edit LoadShape.{self.pvloadshapes[i]} npts=1 mult=[{multiplier}]"
            )
        # TODO: Set multiplier of reactive power based on load_q profile

    def _solve(self, curr_datetime: datetime):
        """Run power flow analysis for a single timestep"""
        time_start = time.time()
        self._set_load_shape_multipliers(curr_datetime)
        self.dss.run_command("Solve")
        Δp, Δq = self._extract_load_pv_powers()
        freqs = [freq := NOMINAL_FREQUENCY]
        for _ in range(MAX_ITERATION):
            new_freq = self._update_freq(freq, Δp)
            self._set_power_storages(Δp, Δq)
            self.dss.run_command("Solve")
            freqs.append(new_freq)
            if abs(new_freq - freq) / NOMINAL_FREQUENCY < SMALL_NUMBER:
                break
            freq = new_freq
        time_end = time.time()
        return time_end - time_start, freq, freqs

    def _extract_power(self, powers):
        if len(powers) < 3:
            return powers[0], powers[1]
        elif len(powers) < 5:
            return (
                powers[0] + powers[2],
                powers[1] + powers[3],
            )
        else:
            return (
                powers[0] + powers[2] + powers[4],
                powers[1] + powers[3] + powers[5],
            )

    def _extract_load_pv_powers(self):
        """Extract powers of loads and PVs"""
        Δp = 0.0
        Δq = 0.0
        for load in self.loads:
            self.dss.Circuit.SetActiveElement(f"Load.{load}")
            dp, dq = self._extract_power(self.dss.CktElement.Powers())
            Δp += dp
            Δq += dq
        for pv in self.pvsystems:
            self.dss.Circuit.SetActiveElement(f"PVSystem.{pv}")
            dp, dq = self._extract_power(self.dss.CktElement.Powers())
            Δp += dp
            Δq += dq
        return Δp, Δq

    def _update_freq(self, freq: float = NOMINAL_FREQUENCY, Δp: float = 0.0):
        """Update the system frequency in the OpenDSS simulation"""
        Δf = -(
            Δp
            * NOMINAL_FREQUENCY
            * NOMINAL_DROOP
            / (len(self.storages) * self.storage_kva)
        )
        return freq + Δf

    def _set_power_storages(self, Δp: float = 0.0, Δq: float = 0.0):
        for storage in self.storages:
            self.dss.Circuit.SetActiveElement(f"Storage.{storage}")
            mult_p = Δp * 3 / (self.storage_kva * len(self.storages))
            new_q_kvar = Δq / len(self.storages)
            cosφ = (Δp + SMALL_NUMBER) / (Δp**2 + Δq**2 + SMALL_NUMBER**2) ** 0.5
            self.dss.run_command(
                f"Edit LoadShape.{storage}Shape npts=1 mult=[{mult_p}]"
            )

    def _get_dict_data(self, klass: str) -> dict:
        """Get all data for a given class as a dictionary"""
        elements = self.__getattribute__(f"{klass}s")
        results = {}
        for element in elements:
            self.dss.Circuit.SetActiveElement(f"{klass}.{element}")
            results[f"{klass}.{element}"] = {
                "bus_names": self.dss.CktElement.BusNames(),
                "powers": self.dss.CktElement.Powers(),
                "voltages": self.dss.CktElement.Voltages(),
                "currents": self.dss.CktElement.Currents(),
            }
        return results

    def _get_voltages(self) -> dict:
        """Get voltages at all buses"""
        voltages_dict = {}
        for bus in self.buses:
            self.dss.Circuit.SetActiveBus(bus)
            voltages_dict[bus] = self.dss.Bus.Voltages()

        return voltages_dict

    def dump_results(
        self,
        delta_time: float,
        curr_datetime: datetime,
        freq: float,
        freqs: list[float],
    ):
        """Dump results to a JSON file for the current timestep"""
        timestamp = curr_datetime.strftime("%Y%m%d_%H%M%S")
        results = {
            "timestamp": curr_datetime.isoformat(),
            "solve_time_ms": delta_time,
            "converged": True if self.dss.Solution.Converged() else False,
            "frequency": freq,
            "frequencies": freqs,
            "losses": self.dss.Circuit.Losses(),
            "voltages": self._get_voltages(),
            "lines": self._get_dict_data("line"),
            "loads": self._get_dict_data("load"),
            "generators": self._get_dict_data("generator"),
            "storages": self._get_dict_data("storage"),
            "pvsystems": self._get_dict_data("pvsystem"),
            "vsources": self._get_dict_data("vsource"),
        }
        cleaned_results = clean_nans(results)
        output_path = os.path.join(OUTPUT_FOLDER, f"results_{timestamp}.json")
        with open(output_path, "w") as f:
            json.dump(cleaned_results, f, indent=4)

    def solve(self, curr_datetime: datetime):
        """Run power flow and extract results"""
        delta_time, freq, freqs = self._solve(curr_datetime)
        self.dump_results(delta_time, curr_datetime, freq=freq, freqs=freqs)


def run_daily_powerflow(
    extra_unit_request: RunDailyExampleRequest = RunDailyExampleRequest(),
    dss_filename: str = "Run_QSTS.dss",
    from_datetime: datetime = datetime(2025, 1, 1),
    to_datetime: datetime = datetime(2025, 1, 2),
):
    """
    Run power flow analysis for each hour of a day using Ray for parallel execution
    """
    cpu_count = psutil.cpu_count() or MAX_CPU_COUNT
    logger.info(f"System has {cpu_count} CPU cores available")

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit(dss_filename)
    profiles = ProfileReader().process_and_record_profiles().get_profiles()

    total_runs = int((to_datetime - from_datetime).total_seconds() // (60 * 15))
    run_indices = list(range(total_runs))
    logger.info(f"Total runs: {total_runs}")

    workers = [
        DSSWorker.remote(
            InputDSSWorker(
                basedir=basedir,
                temp_file=temp_file,
                env_vars=env_vars,
            ),
            profiles,
            extra_unit_request,
        )
        for _ in range(cpu_count - 1)
    ]

    # Dynamic task assignment: assign new run_idx to a worker as soon as it is free
    futures = []
    run_iter = iter(run_indices)

    # Start one task per worker
    for worker in workers:
        try:
            run_idx = next(run_iter)
            futures.append(
                (
                    worker,
                    worker.solve.remote(
                        from_datetime + timedelta(minutes=run_idx * 15),
                    ),
                )
            )
        except StopIteration:
            break

    pbar = tqdm(total=total_runs, desc="Running Power Flows")
    while futures:
        # Wait for any future to complete
        done_ids, _ = ray.wait([f[1] for f in futures])
        done_id = done_ids[0]
        # Find which worker finished
        for i, (worker, future) in enumerate(futures):
            if future == done_id:
                try:
                    ray.get(done_id)
                except Exception as e:
                    logger.error(
                        f"Error in worker id {done_id}: {e}, skipping this run..."
                    )
                    ray.cancel(done_id)
                pbar.update(1)
                # Assign new task to this worker if any left
                try:
                    run_idx = next(run_iter)
                    new_future = worker.solve.remote(
                        from_datetime + timedelta(minutes=run_idx * 15)
                    )
                    futures[i] = (worker, new_future)
                except StopIteration:
                    # No more tasks, remove this worker from the list
                    futures.pop(i)
                break
    pbar.close()
    os.remove(temp_file)
