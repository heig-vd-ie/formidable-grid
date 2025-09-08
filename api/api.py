import time
from flask import Flask, request, jsonify
import os
from api.konfig import *
from api.app import *
from api.parser import *

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/api/time")
def get_current_time():
    return {"time": time.time()}


@app.route("/api/run-powerflow", methods=["POST"])
def run_powerflow_endpoint():
    return run_powerflow()


@app.route("/api/load_cache_data", methods=["POST"])
def load_cache_data_endpoint():
    return load_cache_data()


@app.route("/api/list_cache_files", methods=["GET"])
def list_cache_files_endpoint():
    return list_cache_files()


@app.route("/api/get_node_details", methods=["POST"])
def get_node_details_endpoint():
    return get_node_details()


@app.route("/api/get_link_details", methods=["POST"])
def get_link_details_endpoint():
    return get_link_details()


@app.route("/api/get_simulation_results", methods=["GET"])
def get_simulation_results_endpoint():
    return get_simulation_results()


@app.route("/api/get_data", methods=["GET"])
def get_data_endpoint():
    return get_data()


@app.route("/api/read_glm_file", methods=["POST"])
def read_glm_file():
    """Read GLM file content for editing"""
    try:
        data = request.get_json()
        filename = data.get("filename")

        if not filename:
            return jsonify({"success": False, "error": "No filename provided"}), 400

        file_path = os.path.join(INPUTS_FOLDER_APP, filename)

        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "File not found"}), 404

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return jsonify({"success": True, "content": content, "filename": filename})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/save_glm_file", methods=["POST"])
def save_glm_file():
    """Save GLM file content after editing"""
    try:
        data = request.get_json()
        filename = data.get("filename")
        content = data.get("content")

        if not filename or content is None:
            return (
                jsonify({"success": False, "error": "Filename and content required"}),
                400,
            )

        file_path = os.path.join(INPUTS_FOLDER_APP, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        with open(
            os.path.join(UPLOADS_FOLDER_APP, filename), "w", encoding="utf-8"
        ) as f:
            f.write(content)

        return jsonify(
            {"success": True, "message": f"File {filename} saved successfully"}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/upload_glm_file", methods=["POST"])
def upload_glm_file():
    """Upload GLM file without running simulation"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return jsonify({"success": False, "error": "Empty filename"}), 400

        # Save uploaded file
        file_path = os.path.join(UPLOADS_FOLDER_APP, uploaded_file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        uploaded_file.save(file_path)

        return jsonify(
            {
                "success": True,
                "message": f"File {uploaded_file.filename} uploaded successfully",
                "filename": uploaded_file.filename,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
