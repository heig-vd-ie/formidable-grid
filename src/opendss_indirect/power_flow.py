import os
import psutil
from tqdm import tqdm
from datetime import datetime, timedelta
from konfig import *
from data_model import ElementsSetPoints, FreqCoefficients, GfmKace, ProfileData
from setup_log import setup_logger
from opendss_indirect.worker import DSSWorker
from helpers import (
    remove_json_files,
    setup_opendss_file,
    setup_env_vars,
    to_seconds,
)
import ray

logger = setup_logger(__name__)


def update_freq(el_sps: ElementsSetPoints, freq_coeff: FreqCoefficients):
    """Frequency update based on droop and storage capacity"""
    Δpg = sum(el_sps.pvsystem.p.values()) + sum(el_sps.storage.p.values())
    Δpd = sum(el_sps.load.p.values())
    Δf = (Δpg - Δpd) / (
        freq_coeff.damping * Δpd + sum([1 / r for r in freq_coeff.droop.values()])
    )
    return NOMINAL_FREQUENCY + Δf


def run_qsts_remotely(
    profiles: ProfileData,
    dss_filename: str = "Run_QSTS.dss",
    gfm_kace: GfmKace = GfmKace(),
    from_datetime: datetime = datetime(2025, 1, 1),
    to_datetime: datetime = datetime(2025, 1, 2),
):
    remove_json_files()

    env_vars = {
        "INTERNAL_DSSFILES_FOLDER": INTERNAL_DSSFILES_FOLDER,
        "EXTERNAL_DSSFILES_FOLDER": EXTERNAL_DSSFILES_FOLDER,
        "DSS_EXPORT_FOLDER": DSS_EXPORT_FOLDER,
        "STEP_SIZE": STEP_SIZE,
    }
    setup_env_vars(env_vars)

    temp_filepath = setup_opendss_file(dss_filename)

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
            worker = DSSWorker.remote(temp_filepath, profiles, gfm_kace)
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
    os.remove(temp_filepath)
