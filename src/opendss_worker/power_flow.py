from datetime import datetime, timedelta
import os

import psutil
from tqdm import tqdm

from konfig import *
from data_model import ExtraUnitRequest, InputDSSWorker, ProfileData
from setup_log import setup_logger
from opendss_worker.worker import DSSWorker
from helpers import (
    remove_json_files,
    setup_circuit,
    setup_env_vars,
    to_seconds,
)
import ray

logger = setup_logger(__name__)


def run_qsts_powerflow(
    profiles: ProfileData,
    extra_unit_request: ExtraUnitRequest = ExtraUnitRequest(),
    dss_filename: str = "Run_QSTS.dss",
    from_datetime: datetime = datetime(2025, 1, 1),
    to_datetime: datetime = datetime(2025, 1, 2),
):
    remove_json_files()

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": INTERNAL_DSSFILES_FOLDER,
        "EXTERNAL_DSSFILES_FOLDER": EXTERNAL_DSSFILES_FOLDER,
        "DSS_EXPORT_FOLDER": DSS_EXPORT_FOLDER,
        "STEP_SIZE": STEP_SIZE,
    }
    setup_env_vars(env_vars)

    temp_file = setup_circuit(dss_filename)
    input_dss_worker = InputDSSWorker(basedir, temp_file)

    max_parallel = max(1, (psutil.cpu_count() or MAX_CPU_COUNT) - 1)
    logger.info(f"{max_parallel} CPU cores used")

    total_seconds = to_seconds(STEP_SIZE)

    total_runs = int((to_datetime - from_datetime).total_seconds() // total_seconds)
    logger.info(f"Total runs: {total_runs}")
    timestamps = [
        from_datetime + timedelta(seconds=i * total_seconds) for i in range(total_runs)
    ]

    pbar = tqdm(total=total_runs, desc="Running Power Flows")

    pending = list()
    next_idx = 0

    while next_idx < total_runs or pending:
        # Launch new workers if below CPU limit
        while len(pending) < max_parallel and next_idx < total_runs:
            ts = timestamps[next_idx]
            worker = DSSWorker.remote(input_dss_worker, profiles, extra_unit_request)
            future = worker.solve.remote(ts)
            pending.append(future)
            next_idx += 1
        done, pending = ray.wait(pending, num_returns=1)
        done_id = done[0]
        try:
            ray.get(done_id)
        except Exception as e:
            logger.error(f"Worker failed at {timestamps[next_idx-1]}: {e}")
        pbar.update(1)
    pbar.close()
    os.remove(temp_file)
