from flask import Flask
from flask_restx import Api, Resource
import ray
from ray._private.worker import BaseContext

from common.konfig import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
api = Api(app, doc="/")  # / will show Swagger UI

ns_ray = api.namespace("RAY", description="Ray Operations")


@ns_ray.route("/ray-init")
class RayInit(Resource):
    def get(self):
        if not ray.is_initialized():
            context: BaseContext = ray.init()
            return_result = {
                "status": "Ray initialized",
                "dashboard_url": str(context.dashboard_url),
                "ray_version": str(context.ray_version),
            }
        else:
            return_result = {"status": "Ray already initialized"}
        return return_result


@ns_ray.route("/ray-shutdown")
class RayShutdown(Resource):
    def get(self):
        if ray.is_initialized():
            ray.shutdown()
            return_result = {"status": "Ray shut down"}
        else:
            return_result = {"status": "Ray was not initialized"}
        return return_result
