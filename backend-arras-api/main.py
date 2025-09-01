from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import subprocess
import os
from pathlib import Path

app = FastAPI()

# Folder where GridLAB-D files are stored and run
GRIDLABD_DIR = Path(".cache/arras")
GRIDLABD_DIR_DOCKER = Path("/app/models")
GRIDLABD_DIR.mkdir(exist_ok=True, parents=True)
BACKEND_ARRAS_SERVICE = os.getenv("BACKEND_ARRAS_SERVICE", "backend-arras")


@app.get("/")
def hello():
    return {"message": "Welcome from arras APIs!"}


@app.patch("/run")
async def run_gridlabd(file: UploadFile = File(...)):
    try:
        if file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded")
        # Save uploaded file to the mounted folder
        file_path = GRIDLABD_DIR / file.filename
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        file_path_docker = GRIDLABD_DIR_DOCKER / file.filename
        # Run GridLAB-D on that file
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-it",
                f"{BACKEND_ARRAS_SERVICE}",
                "gridlabd",
                str(file_path_docker),
            ],
            capture_output=True,
            text=True,
        )

        # Return output and errors
        return {
            "filename": file.filename,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
