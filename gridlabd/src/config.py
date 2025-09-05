from flask import Flask
import os


SECRET_KEY = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"

# Configuration
NATIVE_PORT = os.getenv("FRONTEND_GRIDLABD_NATIVE_PORT", "5001")
BACKEND_GRIDLABD_PORT = os.getenv("BACKEND_GRIDLABD_PORT", "4600")
if os.getenv("DEV", "").lower() == "true":
    UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), "../../.cache/uploads")
    MODELS_FOLDER = os.path.join(os.path.dirname(__file__), "../../.cache/models")
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "../../.cache/output")
    BACKEND_GRIDLABD_URL = f"http://localhost:{BACKEND_GRIDLABD_PORT}"
else:
    UPLOADS_FOLDER = os.getenv("UPLOADS_FOLDER", "")
    MODELS_FOLDER = os.getenv("MODELS_FOLDER", "")
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "")
    BACKEND_GRIDLABD_URL = f"http://backend-gridlabd:{BACKEND_GRIDLABD_PORT}"


os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(MODELS_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
