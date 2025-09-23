import time

from flask import Flask
from flask_restx import Api, Resource
import ray

from common.konfig import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
api = Api(app, doc="/docs")  # /docs will show Swagger UI

ns = api.namespace("ray", description="Ray Operations")


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/api/time")
def get_current_time():
    return {"time": time.time()}


@ns.route("/api/ray-init")
class RayInit(Resource):
    def get(self):
        if not ray.is_initialized():
            context = ray.init()
            print(context.dashboard_url)
            return_result = {"status": "Ray initialized"}
        else:
            return_result = {"status": "Ray already initialized"}

        return return_result


@ns.route("/api/ray-shutdown")
class RayShutdown(Resource):
    def get(self):
        if ray.is_initialized():
            ray.shutdown()
            return_result = {"status": "Ray shut down"}
        else:
            return_result = {"status": "Ray was not initialized"}
        return return_result
