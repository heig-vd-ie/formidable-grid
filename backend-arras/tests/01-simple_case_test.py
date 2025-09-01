import os
import pytest
import shutil
from pathlib import Path
import requests

OUTPUT_FOLDER = Path(__file__).parent.parent.parent / ".cache/tests"
url = f"http://localhost:{os.getenv('BACKEND_ARRAS_PORT', 4600)}"


@pytest.fixture(autouse=True)
def clean_output_folder():
    if OUTPUT_FOLDER.exists():
        shutil.rmtree(OUTPUT_FOLDER)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(OUTPUT_FOLDER)


def test_run_gridlabd_creates_output_file():
    dummy_glm = OUTPUT_FOLDER.joinpath("test.glm")
    dummy_glm.write_text("clock { timezone PST8PDT; }")

    with open(dummy_glm, "rb") as f:
        response = requests.patch(
            f"{url}/run", files={"file": ("test.glm", f, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "stdout" in data
    assert "stderr" in data
    assert "returncode" in data

    assert OUTPUT_FOLDER.joinpath("test.glm").exists()


def test_run_gridlabd_123_node():
    dummy_glm = OUTPUT_FOLDER.joinpath("test.glm")
    with open(
        Path(__file__).parent.parent / "data" / "simple-grid.glm",
        "r",
    ) as f:
        dummy_glm.write_text(f.read())

    with open(OUTPUT_FOLDER.joinpath("test.glm"), "rb") as f:
        response = requests.patch(
            f"{url}/run", files={"file": ("test.glm", f, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "stdout" in data
    assert "stderr" in data
    assert "returncode" in data
    assert len(data["stdout"]) == 7058
    assert OUTPUT_FOLDER.joinpath("test.glm").exists()
