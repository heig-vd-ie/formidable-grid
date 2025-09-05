from flask import Flask, render_template, request, session
from konfig import *
from app import *
from parser import *

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page - handles GLM file uploads"""
    handles_file()
    return render_template("index.html")


@app.route("/run-powerflow", methods=["POST"])
def run_powerflow_endpoint():
    return run_powerflow()


@app.route("/load_cache_data", methods=["POST"])
def load_cache_data_endpoint():
    return load_cache_data()


@app.route("/list_cache_files")
def list_cache_files_endpoint():
    return list_cache_files()


@app.route("/get_node_details", methods=["POST"])
def get_node_details_endpoint():
    return get_node_details()


@app.route("/get_link_details", methods=["POST"])
def get_link_details_endpoint():
    return get_link_details()


@app.route("/get_simulation_results", methods=["GET"])
def get_simulation_results_endpoint():
    return get_simulation_results()


if __name__ == "__main__":
    if not SERVER_PORT_NATIVE:
        raise ValueError("SERVER_PORT_NATIVE environment variable is not set")
    app.run(port=int(SERVER_PORT_NATIVE), host="0.0.0.0", debug=True)
