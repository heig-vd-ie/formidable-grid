import os
from flask import Flask, render_template, request, session
from konfig import (
    SECRET_KEY,
    UPLOADS_FOLDER,
    INPUTS_FOLDER,
    OUTPUTS_FOLDER,
    APP_DOCKER_NAME,
    NATIVE_PORT,
)
from app.power_flow import run_powerflow
from parser.glm_folders import list_cache_files, load_cache_data
from parser.glm_res import get_node_details, get_link_details, get_simulation_results

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config["UPLOADS_FOLDER"] = UPLOADS_FOLDER
app.config["INPUTS_FOLDER"] = INPUTS_FOLDER
app.config["OUTPUTS_FOLDER"] = OUTPUTS_FOLDER
app.config["APP_DOCKER_NAME"] = APP_DOCKER_NAME


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page - handles GLM file uploads via form for legacy support"""
    if request.method == "POST":
        # Handle CSV file upload for fixed nodes (optional feature)
        if (
            ("fixedNodes" in request.files)
            and request.files["fixedNodes"]
            and request.files["fixedNodes"].filename
            and (
                request.files["fixedNodes"].filename.rsplit(".", 1)[-1].lower() == "csv"
            )
        ):
            session["csv"] = 1
            fullfilename = os.path.join(app.config["UPLOADS_FOLDER"], "curr.csv")
            request.files["fixedNodes"].save(fullfilename)

        # Handle GLM file upload
        if (
            ("glm_file" in request.files)
            and request.files["glm_file"]
            and request.files["glm_file"].filename
            and (request.files["glm_file"].filename.rsplit(".", 1)[1] == "glm")
        ):
            session.clear()
            session["glm_name"] = request.files["glm_file"].filename
            fullfilename = os.path.join(app.config["UPLOADS_FOLDER"], "curr.glm")
            request.files["glm_file"].save(fullfilename)

    return render_template("index.html")


@app.route("/run-powerflow", methods=["POST"])
def run_powerflow_endpoint():
    return run_powerflow(app.config)


@app.route("/load_cache_data", methods=["POST"])
def load_cache_data_endpoint():
    return load_cache_data(app.config)


@app.route("/list_cache_files")
def list_cache_files_endpoint():
    return list_cache_files(app.config)


@app.route("/get_node_details", methods=["POST"])
def get_node_details_endpoint():
    return get_node_details(app.config)


@app.route("/get_link_details", methods=["POST"])
def get_link_details_endpoint():
    return get_link_details(app.config)


@app.route("/get_simulation_results", methods=["GET"])
def get_simulation_results_endpoint():
    return get_simulation_results(app.config)


if __name__ == "__main__":
    if not NATIVE_PORT:
        raise ValueError("NATIVE_PORT environment variable is not set")
    app.run(port=int(NATIVE_PORT), host="0.0.0.0", debug=True)
