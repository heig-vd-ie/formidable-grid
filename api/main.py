from fastapi import FastAPI
import ray
from ray._private.worker import BaseContext

from app.dss_worker import ray_init, ray_shutdown, read_results, run_daily_powerflow
from app.plotter import create_qsts_plots
from app import _recreate_profile_data

app = FastAPI()


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


@app.get("/run-daily-example")
def run_daily_example(
    total_runs: int = 1,
    number_of_pvs: int = 5,
    pv_capacity_kva_mean: float = 10.0,
    storage_capacity_kw_mean: float = 20.0,
    grid_forming_percent: float = 0.5,
):

    run_daily_powerflow(
        total_runs=total_runs,
        number_of_pvs=number_of_pvs,
        pv_capacity_kva_mean=pv_capacity_kva_mean,
        storage_capacity_kw_mean=storage_capacity_kw_mean,
        grid_forming_percent=grid_forming_percent,
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

    return return_result
