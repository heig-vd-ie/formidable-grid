import os
import shutil
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException

api = FastAPI()

MODELS_FOLDER = os.getenv("MODELS_FOLDER")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")


@api.get("/")
def hello():
    return {"message": "Welcome from GridLabD APIs!"}


@api.patch("/run-powerflow")
async def run_powerflow(file: UploadFile = File(...), randomseed: int = 42):
    try:
        if file.filename is None:
            raise HTTPException(status_code=400, detail="No file uploaded")
        # Save uploaded file to the mounted folder
        if not isinstance(MODELS_FOLDER, str) or not isinstance(OUTPUT_FOLDER, str):
            raise ValueError(
                "MODELS_FOLDER or OUTPUT_FOLDER environment variable is not set"
            )
        file_path_docker = Path(MODELS_FOLDER) / file.filename
        with file_path_docker.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        # Run GridLAB-D on that file
        result = subprocess.run(
            [
                "gridlabd",
                str(file_path_docker),
                "-D",
                "randomseed={}".format(randomseed),
                "-o",
                str(Path(OUTPUT_FOLDER) / f"{Path(file.filename).stem}.json"),
            ],
            cwd=Path(OUTPUT_FOLDER),
            capture_output=True,
            text=True,
        )
        stray_json = Path(MODELS_FOLDER) / (Path(file_path_docker).stem + ".json")
        if stray_json.exists():
            os.remove(stray_json)

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = os.getenv("SERVER_PORT")

    if port is None:
        raise ValueError("SERVER_PORT environment variable is not set")

    uvicorn.run(api, host="0.0.0.0", port=int(port))
