import os
import shutil
import subprocess
from pathlib import Path
from flask import request, jsonify
from api.konfig import *


def run_powerflow():
    """API endpoint for running GridLAB-D simulations"""
    try:
        if "file" not in request.files:
            return jsonify({"detail": "No file uploaded"}), 400

        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return jsonify({"detail": "Empty filename"}), 400

        randomseed = request.form.get("randomseed", 42)

        if not INPUTS_FOLDER:
            raise ValueError("INPUTS_FOLDER environment variable is not set")
        if not OUTPUTS_FOLDER:
            raise ValueError("OUTPUTS_FOLDER environment variable is not set")
        if not APP_DOCKER_NAME:
            raise ValueError("APP_DOCKER_NAME environment variable is not set")

        # Save uploaded file
        file_path = Path(INPUTS_FOLDER_APP) / uploaded_file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("wb") as f:
            shutil.copyfileobj(uploaded_file.stream, f)
        file_path_docker = Path(INPUTS_FOLDER) / uploaded_file.filename

        # Run GridLAB-D
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "-it",
                    APP_DOCKER_NAME,
                    "gridlabd",
                    str(file_path_docker),
                    "-D",
                    f"randomseed={randomseed}",
                    "-o",
                    str(
                        Path(OUTPUTS_FOLDER)
                        / f"{Path(uploaded_file.filename).stem}.json"
                    ),
                ],
                cwd=Path(OUTPUTS_FOLDER_APP),
                capture_output=True,
                text=True,
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Failed to execute GridLAB-D: {str(e)}",
                    }
                ),
                500,
            )

        # Remove stray JSON in models folder
        stray_json = Path(INPUTS_FOLDER_APP) / (Path(file_path_docker).stem + ".json")
        if stray_json.exists():
            os.remove(stray_json)

        if result.returncode == 0:
            output_file = str(
                Path(OUTPUTS_FOLDER_APP) / f"{Path(uploaded_file.filename).stem}.json"
            )
            return jsonify(
                {
                    "success": True,
                    "output_file": output_file,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "error": f"GridLAB-D execution failed: {result.stderr}",
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )

    except Exception as e:
        return jsonify({"detail": str(e)}), 500
