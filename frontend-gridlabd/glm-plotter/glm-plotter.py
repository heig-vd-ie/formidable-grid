from flask import Flask, render_template, request, session, jsonify
import os
import json
import requests
import shutil
import GLMparser

app = Flask(__name__)
app.secret_key = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"

# Configuration
NATIVE_PORT = os.getenv("FRONTEND_GRIDLABD_NATIVE_PORT", "5001")
BACKEND_GRIDLABD_PORT = os.getenv("BACKEND_GRIDLABD_PORT", "4600")
if os.getenv("DEV", "").lower() == "true":
    UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), "../../.cache/uploads")
    MODELS_FOLDER = os.path.join(os.path.dirname(__file__), "../../.cache/models")
    BACKEND_GRIDLABD_URL = f"http://localhost:{BACKEND_GRIDLABD_PORT}"
else:
    UPLOADS_FOLDER = os.getenv("UPLOADS_FOLDER")
    MODELS_FOLDER = os.getenv("MODELS_FOLDER")
    BACKEND_GRIDLABD_URL = f"http://backend-gridlabd:{BACKEND_GRIDLABD_PORT}"

app.config["UPLOADS_FOLDER"] = UPLOADS_FOLDER
app.config["MODELS_FOLDER"] = MODELS_FOLDER

os.makedirs(app.config["UPLOADS_FOLDER"], exist_ok=True)
os.makedirs(app.config["MODELS_FOLDER"], exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    """Main page - handles GLM file uploads via form for legacy support"""
    if request.method == "POST":
        # Handle CSV file upload for fixed nodes (optional feature)
        if (
            ("fixedNodes" in request.files)
            and request.files["fixedNodes"]
            and request.files["fixedNodes"].filename
            and (request.files["fixedNodes"].filename.rsplit(".", 1)[-1].lower() == "csv")
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


@app.route("/run_simulation", methods=["POST"])
def run_simulation():
    """API endpoint for running GridLAB-D simulations"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not uploaded_file.filename or not uploaded_file.filename.lower().endswith(".glm"):
        return jsonify({"success": False, "error": "File must be a GLM file"}), 400

    try:
        # Get randomseed from request or use default
        randomseed = request.form.get("randomseed", 42)
        
        # Prepare file for backend
        files = {
            "file": (uploaded_file.filename, uploaded_file.stream, "application/octet-stream")
        }
        form_data = {"randomseed": randomseed}

        # Call the backend service
        response = requests.patch(f"{BACKEND_GRIDLABD_URL}/run", files=files, data=form_data)

        if response.status_code == 200:
            result = response.json()

            # Check if GridLAB-D execution was successful
            if result["returncode"] == 0:
                # Look for output files in the cache directory
                cache_dir = app.config["MODELS_FOLDER"]
                output_files = []

                if os.path.exists(cache_dir):
                    for file in os.listdir(cache_dir):
                        if file.endswith(".glm"):
                            output_files.append(file)

                return jsonify({
                    "success": True,
                    "message": "GridLAB-D simulation completed successfully",
                    "output_file": output_files[-1] if output_files else "No output file",
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"GridLAB-D simulation failed: {result['stderr']}",
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                }), 400
        else:
            return jsonify({
                "success": False,
                "error": f"Backend service error: {response.text}",
            }), 500

    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Could not connect to backend-gridlabd service",
        }), 503
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

    cache_dir = app.config["MODELS_FOLDER"]
    file_path = os.path.join(cache_dir, filename)

    if not os.path.isfile(file_path):
        return jsonify({"success": False, "error": f"File {filename} not found in cache"}), 404

    try:
        # Copy the cache file to current working file
        current_file_path = os.path.join(app.config["UPLOADS_FOLDER"], "curr.glm")
        shutil.copy2(file_path, current_file_path)

        # Update session
        session["glm_name"] = filename
        session.pop("csv", None)  # Clear CSV session if any

        return jsonify({
            "success": True,
            "message": f"Loaded {filename} from cache",
            "filename": filename,
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Error loading file: {str(e)}"}), 500


@app.route("/list_cache_files")
def list_cache_files():
    """List all GLM files in the cache directory"""
    cache_dir = app.config["MODELS_FOLDER"]
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


@app.route("/get_node_details", methods=["POST"])
def get_node_details():
    """Get detailed information about a specific node (Advanced Option)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    node_name = data.get("node_name")
    if not node_name:
        return jsonify({"error": "No node name provided"}), 400

    try:
        # Load the current GLM file
        glm_file_path = os.path.join(app.config["UPLOADS_FOLDER"], "curr.glm")

        if not os.path.isfile(glm_file_path):
            return jsonify({"error": "No GLM file loaded"}), 404

        # Parse the GLM file to get detailed object information
        objs, modules, commands = GLMparser.readGLM(glm_file_path)

        # Find the node object(s) with the given name
        node_objects = [obj for obj in objs if obj.get("name") == node_name]

        if not node_objects:
            # Try to find by parent relationship or other name fields
            node_objects = [obj for obj in objs if obj.get("name_oldGLM") == node_name]

        if not node_objects:
            return jsonify({"error": f"Node {node_name} not found"}), 404

        # Get the main node object
        main_node = node_objects[0]

        # Find child objects (like generators, capacitors, etc.)
        child_objects = [obj for obj in objs if obj.get("parent") == node_name]

        # Find connected elements (lines, transformers, etc.)
        connections = []
        link_types = [
            "overhead_line", "switch", "underground_line", "regulator",
            "transformer", "triplex_line", "fuse"
        ]

        for obj in objs:
            if obj.get("class") in link_types:
                if obj.get("from") == node_name:
                    connections.append({
                        "name": obj.get("to", "Unknown"),
                        "type": "to",
                        "linkType": obj.get("class"),
                        "object": obj,
                    })
                elif obj.get("to") == node_name:
                    connections.append({
                        "name": obj.get("from", "Unknown"),
                        "type": "from",
                        "linkType": obj.get("class"),
                        "object": obj,
                    })

        # Extract properties from the main node (excluding metadata)
        properties = {}
        excluded_keys = {"name", "class", "startLine", "name_oldGLM", "parent"}

        for key, value in main_node.items():
            if key not in excluded_keys:
                properties[key] = value

        # Add child object properties
        child_properties = {}
        for child in child_objects:
            child_name = child.get("class", "child")
            child_props = {}
            for key, value in child.items():
                if key not in excluded_keys:
                    child_props[key] = value
            if child_props:
                child_properties[child_name] = child_props

        # Prepare response
        response_data = {
            "name": node_name,
            "class": main_node.get("class"),
            "properties": properties if properties else None,
            "child_properties": child_properties if child_properties else None,
            "connections": connections if connections else None,
            "children": (
                [child.get("class") for child in child_objects]
                if child_objects else None
            ),
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Error retrieving node details: {str(e)}"}), 500


@app.route("/get_link_details", methods=["POST"])
def get_link_details():
    """Get detailed information about a specific link/line (Advanced Option)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    source_node = data.get("source")
    target_node = data.get("target")
    link_type = data.get("link_type")

    if not source_node or not target_node:
        return jsonify({"error": "Source and target nodes required"}), 400

    try:
        # Load the current GLM file
        glm_file_path = os.path.join(app.config["UPLOADS_FOLDER"], "curr.glm")

        if not os.path.isfile(glm_file_path):
            return jsonify({"error": "No GLM file loaded"}), 404

        # Parse the GLM file to get detailed object information
        objs, modules, commands = GLMparser.readGLM(glm_file_path)

        # Find the link object with the given from/to nodes
        link_objects = []
        for obj in objs:
            if obj.get("class") == link_type and (
                (obj.get("from") == source_node and obj.get("to") == target_node)
                or (obj.get("from") == target_node and obj.get("to") == source_node)
            ):
                link_objects.append(obj)

        if not link_objects:
            return jsonify({
                "error": f"Link between {source_node} and {target_node} not found"
            }), 404

        # Get the main link object
        main_link = link_objects[0]

        # Extract properties from the main link (excluding metadata)
        properties = {}
        excluded_keys = {"name", "class", "startLine", "name_oldGLM", "parent", "from", "to"}

        for key, value in main_link.items():
            if key not in excluded_keys:
                properties[key] = value

        # Prepare response
        response_data = {
            "name": main_link.get("name", f"{source_node}-{target_node}"),
            "class": main_link.get("class"),
            "from": main_link.get("from"),
            "to": main_link.get("to"),
            "properties": properties if properties else None,
            "type": "link",
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Error retrieving link details: {str(e)}"}), 500


@app.route("/get_simulation_results", methods=["GET"])
def get_simulation_results():
    """Get simulation results from cache folder (Advanced Option)"""
    try:
        models_dir = app.config["MODELS_FOLDER"]

        # First try to get results from JSON file (preferred)
        json_files = [f for f in os.listdir(models_dir) if f.endswith(".json")]

        if json_files:
            # Use the first JSON file found
            json_file = os.path.join(models_dir, json_files[0])

            with open(json_file, "r") as f:
                data = json.load(f)

            results = []
            objects = data.get("objects", {})

            for obj_name, obj_data in objects.items():
                if obj_data.get("class") in [
                    "node", "load", "meter", "triplex_meter", "triplex_node"
                ]:
                    # Extract voltage data
                    voltage_A = obj_data.get("voltage_A", "0+0j V")
                    voltage_B = obj_data.get("voltage_B", "0+0j V")
                    voltage_C = obj_data.get("voltage_C", "0+0j V")

                    # Parse complex voltage values
                    def parse_voltage(v_str):
                        if isinstance(v_str, str):
                            # Remove 'V' and parse complex number
                            v_clean = v_str.replace("V", "").strip()
                            if "j" in v_clean:
                                try:
                                    return complex(v_clean.replace("j", "j"))
                                except:
                                    return complex(0)
                            else:
                                try:
                                    return complex(float(v_clean))
                                except:
                                    return complex(0)
                        return complex(0)

                    volt_a = parse_voltage(voltage_A)
                    volt_b = parse_voltage(voltage_B)
                    volt_c = parse_voltage(voltage_C)

                    # Calculate magnitudes
                    mag_a = abs(volt_a)
                    mag_b = abs(volt_b)
                    mag_c = abs(volt_c)

                    # Calculate overall voltage magnitude (max of phases)
                    voltage_magnitude = max(mag_a, mag_b, mag_c)

                    # Get nominal voltage (assuming 2401.78V line-to-neutral)
                    nominal_voltage = 2401.78
                    voltage_percent = (
                        (voltage_magnitude / nominal_voltage) * 100
                        if voltage_magnitude > 0 else 0
                    )

                    result_row = {
                        "node": obj_name,
                        "class": obj_data.get("class", ""),
                        "bustype": obj_data.get("bustype", ""),
                        "phases": obj_data.get("phases", ""),
                        "nominal_voltage": nominal_voltage,
                        "voltage_A_mag": mag_a,
                        "voltage_B_mag": mag_b,
                        "voltage_C_mag": mag_c,
                        "voltage_magnitude": voltage_magnitude,
                        "voltage_percent": voltage_percent,
                        "latitude": obj_data.get("latitude", ""),
                        "longitude": obj_data.get("longitude", ""),
                    }
                    results.append(result_row)

            return jsonify({
                "success": True,
                "source": "json",
                "file": json_files[0],
                "results": results,
                "total_nodes": len(results),
            })

        else:
            return jsonify({"error": "No simulation results found"}), 404

    except Exception as e:
        return jsonify({"error": f"Error reading simulation results: {str(e)}"}), 500


@app.route("/data")
def data():
    """Legacy endpoint for visualization data"""
    glmFile = os.path.join(app.config["UPLOADS_FOLDER"], "curr.glm")
    csvFile = os.path.join(app.config["UPLOADS_FOLDER"], "curr.csv")
    
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
        '{"file":"' + glm_name + '","graph":' + graphJSON + 
        ',"fixedNodes":' + fixedNodesJSON + "}"
    )

    return JSONstr


def parseFixedNodes(nodesFile):
    """Parse CSV file with fixed node coordinates (Advanced Option)"""
    with open(nodesFile) as fr:
        lines = fr.readlines()
    names = []
    x = []
    y = []
    for line in lines:
        parts = line.split(",")
        if len(parts) == 3:
            names.append(parts[0])
            x.append(float(parts[1]))
            y.append(float(parts[2]))

    return json.dumps({"names": names, "x": x, "y": y})


if __name__ == "__main__":
    app.run(port=int(NATIVE_PORT), host="0.0.0.0", debug=True)
