import os
import shutil
from flask import jsonify, request, session


def list_cache_files(cache_dir: str):
    """List all GLM files in the cache directory"""
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


def load_cache_data(cache_dir: str, upload_folder: str):
    """Load a GLM file from cache for visualization"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON data provided"}), 400

    filename = data.get("filename")
    if not filename:
        return jsonify({"success": False, "error": "No filename provided"}), 400

    file_path = os.path.join(cache_dir, filename)

    if not os.path.isfile(file_path):
        return (
            jsonify({"success": False, "error": f"File {filename} not found in cache"}),
            404,
        )

    try:
        # Copy the cache file to current working file
        current_file_path = os.path.join(upload_folder, "curr.glm")
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
