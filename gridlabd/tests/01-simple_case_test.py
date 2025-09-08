import os
import pytest
import shutil
from pathlib import Path
import requests

OUTPUTS_FOLDER = Path(__file__).parent.parent.parent / "data/tests"
url = f"http://localhost:{os.getenv('SERVER_PORT')}"


@pytest.fixture(autouse=True)
def clean_output_folder():
    if OUTPUTS_FOLDER.exists():
        shutil.rmtree(OUTPUTS_FOLDER)
    OUTPUTS_FOLDER.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(OUTPUTS_FOLDER)


def test_run_gridlabd_creates_output_file():
    dummy_glm = OUTPUTS_FOLDER.joinpath("test.glm")
    dummy_glm.write_text("clock { timezone PST8PDT; }")

    with open(dummy_glm, "rb") as f:
        response = requests.post(
            f"{url}/run-powerflow", files={"file": ("test.glm", f, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "stdout" in data
    assert "stderr" in data
    assert "returncode" in data

    assert OUTPUTS_FOLDER.joinpath("test.glm").exists()


def test_run_gridlabd_123_node():
    dummy_glm = OUTPUTS_FOLDER.joinpath("test.glm")
    with open(
        Path(__file__).parent.parent.parent / "inputs" / "data" / "simple-grid.glm",
        "r",
    ) as f:
        dummy_glm.write_text(f.read())

    with open(OUTPUTS_FOLDER.joinpath("test.glm"), "rb") as f:
        response = requests.post(
            f"{url}/run-powerflow", files={"file": ("test.glm", f, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "stdout" in data
    assert "stderr" in data
    assert "returncode" in data
    assert len(data["stdout"]) == 7058
    assert OUTPUTS_FOLDER.joinpath("test.glm").exists()
