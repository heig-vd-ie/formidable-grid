from flask import Flask, render_template, request, session, jsonify
import os
import shutil
from konfig import *
from app import *
from parser import *
from parser.glm_folders import get_data

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page - handles GLM file uploads"""
    if request.method == "POST":
        # Handle CSV file upload for fixed nodes
        if (
            ("fixedNodes" in request.files)
            and request.files["fixedNodes"]
            and request.files["fixedNodes"].filename
            and (
                request.files["fixedNodes"].filename.rsplit(".", 1)[-1].lower() == "csv"
            )
        ):
            session["csv"] = 1
            fullfilename = os.path.join(UPLOADS_FOLDER_APP, "curr.csv")
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
            fullfilename = os.path.join(UPLOADS_FOLDER_APP, "curr.glm")
            request.files["glm_file"].save(fullfilename)
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


@app.route("/data", methods=["GET"])
def get_data_endpoint():
    return get_data()


@app.route("/read_glm_file", methods=["POST"])
def read_glm_file():
    """Read GLM file content for editing"""
    try:
        data = request.get_json()
        filename = data.get("filename")

        if not filename:
            return jsonify({"success": False, "error": "No filename provided"}), 400

        file_path = os.path.join(UPLOADS_FOLDER_APP, filename)

        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": "File not found"}), 404

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return jsonify({"success": True, "content": content, "filename": filename})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/save_glm_file", methods=["POST"])
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

        file_path = os.path.join(UPLOADS_FOLDER_APP, filename)

        # Create backup of original file
        if os.path.exists(file_path):
            backup_path = file_path + ".backup"
            shutil.copy2(file_path, backup_path)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return jsonify(
            {"success": True, "message": f"File {filename} saved successfully"}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/upload_glm_file", methods=["POST"])
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


if __name__ == "__main__":
    if not SERVER_PORT_NATIVE:
        raise ValueError("SERVER_PORT_NATIVE environment variable is not set")
    app.run(port=int(SERVER_PORT_NATIVE), host="0.0.0.0", debug=True)
