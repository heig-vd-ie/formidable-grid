import time

from flask import Flask
import ray

from common.konfig import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/api/time")
def get_current_time():
    return {"time": time.time()}


@app.route("/api/ray-init")
def init_ray():
    if not ray.is_initialized():
        ray.init()
        return_result = {"status": "Ray initialized"}
    else:
        return_result = {"status": "Ray already initialized"}

    return return_result


@app.route("/api/ray-shutdown")
def shutdown_ray():
    if ray.is_initialized():
        ray.shutdown()
        return_result = {"status": "Ray shut down"}
    else:
        return_result = {"status": "Ray was not initialized"}

    return return_result
