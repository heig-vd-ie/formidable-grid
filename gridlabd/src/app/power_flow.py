import os
import shutil
import subprocess
from pathlib import Path
from flask import request, jsonify, Config


def run_powerflow(konfig: Config):
    """API endpoint for running GridLAB-D simulations"""
    try:
        if "file" not in request.files:
            return jsonify({"detail": "No file uploaded"}), 400

        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return jsonify({"detail": "Empty filename"}), 400

        randomseed = request.form.get("randomseed", 42)

        if not isinstance(konfig["INPUTS_FOLDER"], str) or not isinstance(
            konfig["OUTPUTS_FOLDER"], str
        ):
            raise ValueError(
                "INPUTS_FOLDER or OUTPUTS_FOLDER environment variable is not set"
            )

        if not isinstance(konfig["APP_DOCKER_NAME"], str):
            raise ValueError("APP_DOCKER_NAME environment variable is not set")

        # Save uploaded file
        file_path_docker = Path(konfig["INPUTS_FOLDER"]) / uploaded_file.filename
        file_path_docker.parent.mkdir(parents=True, exist_ok=True)
        with file_path_docker.open("wb") as f:
            shutil.copyfileobj(uploaded_file.stream, f)

        # Run GridLAB-D
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                konfig["APP_DOCKER_NAME"],
                "gridlabd",
                str(file_path_docker),
                "-D",
                f"randomseed={randomseed}",
                "-o",
                str(
                    Path(konfig["OUTPUTS_FOLDER"])
                    / f"{Path(uploaded_file.filename).stem}.json"
                ),
            ],
            cwd=Path(konfig["OUTPUTS_FOLDER"]),
            capture_output=True,
            text=True,
        )

        # Remove stray JSON in models folder
        stray_json = Path(konfig["OUTPUTS_FOLDER"]) / (
            Path(file_path_docker).stem + ".json"
        )
        if stray_json.exists():
            os.remove(stray_json)

        return jsonify(
            {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )

    except Exception as e:
        return jsonify({"detail": str(e)}), 500
