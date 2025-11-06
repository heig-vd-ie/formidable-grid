import datetime
from fastapi import FastAPI, Depends
import ray
from ray._private.worker import BaseContext
from datetime import datetime

from app import (
    _recreate_profile_data,
    ray_init,
    ray_shutdown,
    read_results,
    run_daily_powerflow,
    ExtraUnitRequest,
    create_qsts_plots,
)
from app.common.setup_log import setup_logger
from app.extract_data.profile_reader import ProfileReader

app = FastAPI()

logger = setup_logger(__name__)


@app.get("/ray-init")
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


@app.get("/ray-shutdown")
def ray_shutdown_ep():
    if ray.is_initialized():
        ray_shutdown()
        return_result = {"status": "Ray shut down"}
    else:
        return_result = {"status": "Ray was not initialized"}
    return return_result


@app.patch("/recreate-profile-data")
def recreate_profile_data():
    _recreate_profile_data()
    return {"status": "Profile data recreated successfully"}


@app.patch("/get-profile-data")
def get_profile_data():
    return ProfileReader().process_and_record_profiles().get_profiles()


@app.get("/run-daily-example")
def run_daily_example(
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

    profiles = get_profile_data()

    run_daily_powerflow(
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
