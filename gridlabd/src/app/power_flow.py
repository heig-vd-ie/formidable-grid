from flask import request, jsonify
import requests
import os


def run_powerflow(cache_dir: str, BACKEND_GRIDLABD_URL: str):
    """API endpoint for running GridLAB-D simulations"""
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
            f"{BACKEND_GRIDLABD_URL}/run-powerflow", files=files, data=form_data
        )

        if response.status_code == 200:
            result = response.json()

            # Check if GridLAB-D execution was successful
            if result["returncode"] == 0:
                # Look for output files in the cache directory
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
