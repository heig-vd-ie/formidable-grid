from flask import Flask, render_template, request, session, jsonify
import os
import json
import requests
import GLMparser

app = Flask(__name__)
app.secret_key = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"

SERVER_PORT = os.getenv("SERVER_PORT", "5000")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
BACKEND_GRIDLABD_PORT = os.getenv("BACKEND_GRIDLABD_PORT", "4600")
BACKEND_GRIDLABD_URL = f"http://{SERVER_HOST}:{BACKEND_GRIDLABD_PORT}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if (
            ("fixedNodes" in request.files)
            and request.files["fixedNodes"]
            and request.files["fixedNodes"].filename
            and (
                request.files["fixedNodes"].filename.rsplit(".", 1)[-1].lower() == "csv"
            )
        ):
            print("Reading the csv file")
            session["csv"] = 1
            fullfilename = os.path.join(app.config["UPLOAD_FOLDER"], "curr.csv")
            request.files["fixedNodes"].save(fullfilename)

        if (
            ("glm_file" in request.files)
            and request.files["glm_file"]
            and request.files["glm_file"].filename
            and (request.files["glm_file"].filename.rsplit(".", 1)[1] == "glm")
        ):
            print("Reading the glm file")
            session.clear()
            session["glm_name"] = request.files["glm_file"].filename
            fullfilename = os.path.join(app.config["UPLOAD_FOLDER"], "curr.glm")
            request.files["glm_file"].save(fullfilename)

    return render_template("index.html")


@app.route("/run_simulation", methods=["POST"])
def run_simulation():
    """API endpoint for running simulations"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not uploaded_file.filename or not uploaded_file.filename.lower().endswith(
        ".glm"
    ):
        return jsonify({"success": False, "error": "File must be a GLM file"}), 400

    try:
        # Get randomseed from request or use default
        randomseed = request.form.get("randomseed", 42)

        # Prepare file for backend
        files = {
            "file": (
                uploaded_file.filename,
                uploaded_file.stream,
                "application/octet-stream",
            )
        }

        form_data = {"randomseed": randomseed}

        # Call the backend service
        response = requests.patch(
            f"{BACKEND_GRIDLABD_URL}/run", files=files, data=form_data
        )

        if response.status_code == 200:
            result = response.json()

            # Check if GridLAB-D execution was successful
            if result["returncode"] == 0:
                # Look for output files in the cache directory
                cache_dir = app.config["CACHE_FOLDER"]
                output_files = []

                if os.path.exists(cache_dir):
                    for file in os.listdir(cache_dir):
                        if file.endswith(".glm"):
                            output_files.append(file)

                return jsonify(
                    {
                        "success": True,
                        "message": "GridLAB-D simulation completed successfully",
                        "output_file": (
                            output_files[-1] if output_files else "No output file"
                        ),
                        "stdout": result["stdout"],
                        "stderr": result["stderr"],
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"GridLAB-D simulation failed: {result['stderr']}",
                            "stdout": result["stdout"],
                            "stderr": result["stderr"],
                        }
                    ),
                    400,
                )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Backend service error: {response.text}",
                    }
                ),
                500,
            )

    except requests.exceptions.ConnectionError:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Could not connect to backend-gridlabd service",
                }
            ),
            503,
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500


@app.route("/load_cache_data", methods=["POST"])
def load_cache_data():
    """Load a GLM file from cache for visualization"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON data provided"}), 400

    filename = data.get("filename")
    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400

    cache_dir = app.config["CACHE_FOLDER"]
    file_path = os.path.join(cache_dir, filename)

    if not os.path.isfile(file_path):
        return (
            jsonify({"success": False, "error": f"File {filename} not found in cache"}),
            404,
        )

    try:
        # Copy the cache file to current working file
        import shutil

        current_file_path = os.path.join(app.config["UPLOAD_FOLDER"], "curr.glm")
        shutil.copy2(file_path, current_file_path)

        # Update session
        session["glm_name"] = filename
        session.pop("csv", None)  # Clear CSV session if any

        return jsonify(
            {
                "success": True,
                "message": f"Loaded {filename} from cache",
                "filename": filename,
            }
        )

    except Exception as e:
        return (
            jsonify({"success": False, "error": f"Error loading file: {str(e)}"}),
            500,
        )


@app.route("/run_gridlabd", methods=["POST"])
def run_gridlabd():
    """Run GridLAB-D simulation on the uploaded GLM file"""
    glm_file_path = os.path.join(app.config["UPLOAD_FOLDER"], "curr.glm")

    if not os.path.isfile(glm_file_path):
        return jsonify({"error": "No GLM file found. Please upload a file first."}), 400

    try:
        # Read the GLM file and send it to the backend
        with open(glm_file_path, "rb") as f:
            files = {
                "file": (os.path.basename(glm_file_path), f, "application/octet-stream")
            }

            # Get randomseed from request or use default
            randomseed = request.form.get("randomseed", 42)
            data = {"randomseed": randomseed}

            # Call the backend service
            response = requests.patch(
                f"{BACKEND_GRIDLABD_URL}/run", files=files, data=data
            )

        if response.status_code == 200:
            result = response.json()

            # Check if GridLAB-D execution was successful
            if result["returncode"] == 0:
                # Look for output files in the cache directory
                cache_dir = app.config["CACHE_FOLDER"]
                output_files = []

                if os.path.exists(cache_dir):
                    for file in os.listdir(cache_dir):
                        if file.endswith(".glm"):
                            output_files.append(file)

                return jsonify(
                    {
                        "success": True,
                        "message": "GridLAB-D simulation completed successfully",
                        "stdout": result["stdout"],
                        "stderr": result["stderr"],
                        "output_files": output_files,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "GridLAB-D simulation failed",
                            "stdout": result["stdout"],
                            "stderr": result["stderr"],
                        }
                    ),
                    400,
                )
        else:
            return jsonify({"error": f"Backend service error: {response.text}"}), 500

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to backend-gridlabd service"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/run_gridlabd_with_file", methods=["POST"])
def run_gridlabd_with_file():
    """Run GridLAB-D simulation on an uploaded file"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not uploaded_file.filename or not uploaded_file.filename.lower().endswith(
        ".glm"
    ):
        return jsonify({"error": "File must be a GLM file"}), 400

    try:
        # Get randomseed from request or use default
        randomseed = request.form.get("randomseed", 42)

        # Prepare file for backend
        files = {
            "file": (
                uploaded_file.filename,
                uploaded_file.stream,
                "application/octet-stream",
            )
        }

        form_data = {"randomseed": randomseed}

        # Call the backend service
        response = requests.patch(
            f"{BACKEND_GRIDLABD_URL}/run", files=files, data=form_data
        )

        if response.status_code == 200:
            result = response.json()

            # Check if GridLAB-D execution was successful
            if result["returncode"] == 0:
                # Look for output files in the cache directory
                cache_dir = app.config["CACHE_FOLDER"]
                output_files = []

                if os.path.exists(cache_dir):
                    for file in os.listdir(cache_dir):
                        if file.endswith(".glm"):
                            output_files.append(file)

                return jsonify(
                    {
                        "success": True,
                        "message": "GridLAB-D simulation completed successfully",
                        "stdout": result["stdout"],
                        "stderr": result["stderr"],
                        "output_files": output_files,
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "GridLAB-D simulation failed",
                            "stdout": result["stdout"],
                            "stderr": result["stderr"],
                        }
                    ),
                    400,
                )
        else:
            return jsonify({"error": f"Backend service error: {response.text}"}), 500

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Could not connect to backend-gridlabd service"}), 503
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/load_cache_file", methods=["POST"])
def load_cache_file():
    """Load a GLM file from the cache directory"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    cache_dir = app.config["CACHE_FOLDER"]
    file_path = os.path.join(cache_dir, filename)

    if not os.path.isfile(file_path):
        return jsonify({"error": f"File {filename} not found in cache"}), 404

    try:
        # Copy the cache file to current working file
        import shutil

        current_file_path = os.path.join(app.config["UPLOAD_FOLDER"], "curr.glm")
        shutil.copy2(file_path, current_file_path)

        # Update session
        session["glm_name"] = filename
        session.pop("csv", None)  # Clear CSV session if any

        return jsonify(
            {
                "success": True,
                "message": f"Loaded {filename} from cache",
                "filename": filename,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Error loading file: {str(e)}"}), 500


@app.route("/list_cache_files")
def list_cache_files():
    """List all GLM files in the cache directory"""
    cache_dir = app.config["CACHE_FOLDER"]
    files = []

    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            if file.endswith(".glm"):
                file_path = os.path.join(cache_dir, file)
                file_info = {
                    "name": file,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path),
                }
                files.append(file_info)

    return jsonify({"files": files})


@app.route("/data")
def data():
    glmFile = os.path.join(app.config["UPLOAD_FOLDER"], "curr.glm")
    csvFile = os.path.join(app.config["UPLOAD_FOLDER"], "curr.csv")
    if "csv" in session and session["csv"] and os.path.isfile(csvFile):
        fixedNodesJSON = parseFixedNodes(csvFile)
    else:
        fixedNodesJSON = '{"names":[], "x":[], "y":[]}'
    if os.path.isfile(glmFile):
        objs, modules, commands = GLMparser.readGLM(glmFile)
        graphJSON = GLMparser.createD3JSON(objs)
    else:
        graphJSON = '{"nodes":[],"links":[]}'
    if "glm_name" in session:
        glm_name = session["glm_name"]
    else:
        glm_name = ""
    JSONstr = (
        '{"file":"'
        + glm_name
        + '","graph":'
        + graphJSON
        + ',"fixedNodes":'
        + fixedNodesJSON
        + "}"
    )

    return JSONstr


app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(__file__), "../../.cache/uploads"
)
app.config["CACHE_FOLDER"] = os.path.join(
    os.path.dirname(__file__), "../../.cache/gridlabd"
)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["CACHE_FOLDER"], exist_ok=True)


def parseFixedNodes(nodesFile):
    with open(nodesFile) as fr:
        lines = fr.readlines()
    names = []
    x = []
    y = []
    for line in lines:
        bla = line.split(",")
        if len(bla) == 3:
            names.append(bla[0])
            x.append(float(bla[1]))
            y.append(float(bla[2]))

    return json.dumps({"names": names, "x": x, "y": y})


if __name__ == "__main__":
    app.run(port=int(SERVER_PORT), host=SERVER_HOST, debug=True)
