import datetime
from datetime import datetime

from fastapi import Depends, FastAPI
from ray._private.worker import BaseContext

from opendss_worker import (
    ray_init,
    ray_shutdown,
    run_qsts_powerflow,
)
from data_extract import read_results
from data_model import ExtraUnitRequest
from data_display import create_qsts_plots
from data_load import _recreate_profile_data
from setup_log import setup_logger

from data_load.profile_reader import ProfileReader
import ray

app = FastAPI()

logger = setup_logger(__name__)


@app.get("/ray-init", description="Initialize the ray server", tags=["Ray"])
def ray_init_ep():
    if not ray.is_initialized():
        context: BaseContext = ray_init()
        return_result = {
            "status": "Ray initialized",
            "dashboard_url": str(context.dashboard_url),
            "ray_version": str(context.ray_version),
        }
    else:
        return_result = {"status": "Ray already initialized"}
    return return_result


@app.get("/ray-shutdown", description="Shutdown the ray server", tags=["Ray"])
def ray_shutdown_ep():
    if ray.is_initialized():
        ray_shutdown()
        return_result = {"status": "Ray shut down"}
    else:
        return_result = {"status": "Ray was not initialized"}
    return return_result


@app.patch(
    "/recreate-profile-data",
    description="Recreate parqut files for load profiles in data/inputs",
    tags=["PowerProfiles"],
)
def recreate_profile_data():
    _recreate_profile_data()
    return {"status": "Profile data recreated successfully"}


@app.patch(
    "/read-profile-data",
    description="Read power profiles",
    tags=["PowerProfiles"],
)
def read_profile_data():
    return ProfileReader().process_and_record_profiles().read_profiles()


@app.get(
    "/run-qsts",
    description="Run quasi static timeseries power flow for a period of time",
    tags=["QSTS"],
)
def run_qsts(
    from_datetime: datetime = datetime(2025, 1, 1, 0, 0, 0),
    to_datetime: datetime = datetime(2025, 1, 2, 0, 0, 0),
    config: ExtraUnitRequest = Depends(ExtraUnitRequest),
):
    if isinstance(from_datetime, str):
        from_datetime = datetime.fromisoformat(from_datetime)
    if isinstance(to_datetime, str):
        to_datetime = datetime.fromisoformat(to_datetime)

    if not ray.is_initialized():
        ray_init()
        logger.info("Ray was not initialized, initializing now...")
    else:
        logger.info("Ray is already initialized")

    profiles = read_profile_data()

    run_qsts_powerflow(
        profiles=profiles,
        from_datetime=from_datetime,
        to_datetime=to_datetime,
        extra_unit_request=config,
    )
    df = read_results()
    create_qsts_plots(df)

    if df is not None and df.shape[0] >= 1:
        return_result = {
            "status": "Daily power flow run completed successfully",
            "rows": df.shape[0],
        }
    else:
        return_result = {"status": "Failed to read results or no data found"}, 500
    ray_shutdown()
    return return_result
