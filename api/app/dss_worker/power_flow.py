from datetime import datetime, timedelta
import os

import psutil
from tqdm import tqdm

from app.common.konfig import MAX_CPU_COUNT
from app.common.models import ExtraUnitRequest, InputDSSWorker, ProfileData
from app.common.setup_log import setup_logger
from app.dss_worker.worker import DSSWorker
from app.common.helpers import remove_json_files, setup_circuit
import ray

logger = setup_logger(__name__)


def run_daily_powerflow(
    profiles: ProfileData,
    extra_unit_request: ExtraUnitRequest = ExtraUnitRequest(),
    dss_filename: str = "Run_QSTS.dss",
    from_datetime: datetime = datetime(2025, 1, 1),
    to_datetime: datetime = datetime(2025, 1, 2),
):
    remove_json_files()

    basedir = os.getcwd()
    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": os.environ.get("INTERNAL_DSSFILES_FOLDER", ""),
        "DSS_EXPORT_FOLDER": os.environ.get("DSS_EXPORT_FOLDER", ""),
        "EXTERNAL_DSSFILES_FOLDER": os.environ.get("EXTERNAL_DSSFILES_FOLDER", ""),
    }

    temp_file = setup_circuit(dss_filename)
    input_dss_worker = InputDSSWorker(basedir, temp_file, env_vars)

    max_parallel = max(1, (psutil.cpu_count() or MAX_CPU_COUNT) - 1)
    logger.info(f"{max_parallel} CPU cores used")

    total_runs = int((to_datetime - from_datetime).total_seconds() // (60 * 15))
    logger.info(f"Total runs: {total_runs}")
    timestamps = [from_datetime + timedelta(minutes=i * 15) for i in range(total_runs)]

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
