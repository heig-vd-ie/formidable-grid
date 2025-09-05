import os
import shutil
import json
import pandas as pd
from flask import jsonify, request, session
from parser.glm_inp import readGLM, createD3JSON
from konfig import *


def list_cache_files():
    """List all GLM files in the cache directory"""
    files = []

    cache_dir = OUTPUTS_FOLDER_APP
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


def load_cache_data():
    """Load a GLM file from cache for visualization"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON data provided"}), 400

    filename = data.get("filename")
    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400

    file_path = os.path.join(OUTPUTS_FOLDER_APP, filename)

    if not os.path.isfile(file_path):
        return (
            jsonify({"success": False, "error": f"File {filename} not found in cache"}),
            404,
        )

    try:
        # Copy the cache file to current working file
        current_file_path = os.path.join(UPLOADS_FOLDER_APP, "curr.glm")
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


def get_data():
    """Get data for D3.js visualization"""
    try:
        # Check if we have a current GLM file
        current_file_path = os.path.join(UPLOADS_FOLDER_APP, "curr.glm")

        if not os.path.isfile(current_file_path):
            return jsonify({"error": "No GLM file loaded"}), 404

        # Get the filename from session or use default
        filename = session.get("glm_name", "curr.glm")

        # Parse the GLM file
        objs, modules, commands = readGLM(current_file_path)

        # Create D3.js formatted data
        graph_json_str = createD3JSON(objs)
        graph_data = json.loads(graph_json_str)

        # Handle fixed nodes from CSV if available
        fixed_nodes = {"names": [], "x": [], "y": []}
        csv_file_path = os.path.join(UPLOADS_FOLDER_APP, "curr.csv")

        if os.path.isfile(csv_file_path) and session.get("csv"):
            try:
                df = pd.read_csv(csv_file_path)
                if "name" in df.columns and "x" in df.columns and "y" in df.columns:
                    fixed_nodes["names"] = df["name"].tolist()
                    fixed_nodes["x"] = df["x"].tolist()
                    fixed_nodes["y"] = df["y"].tolist()
            except Exception as e:
                print(f"Warning: Could not load CSV file: {e}")

        # Return the data in the format expected by the frontend
        return jsonify(
            {"file": filename, "graph": graph_data, "fixedNodes": fixed_nodes}
        )

    except Exception as e:
        return jsonify({"error": f"Error processing data: {str(e)}"}), 500
