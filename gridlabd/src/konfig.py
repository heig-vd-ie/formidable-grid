from flask import Flask
import os


SECRET_KEY = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"

APP_DOCKER_NAME = os.getenv("APP_DOCKER_NAME")
NATIVE_PORT = os.getenv("SERVER_PORT_NATIVE")
if os.getenv("DEV", "").lower() == "true":
    UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), "../../data/uploads")
    INPUTS_FOLDER = os.path.join(os.path.dirname(__file__), "../../data/inputs")
    OUTPUTS_FOLDER = os.path.join(os.path.dirname(__file__), "../../data/outputs")
else:
    UPLOADS_FOLDER = os.getenv("UPLOADS_FOLDER", "")
    INPUTS_FOLDER = os.getenv("INPUTS_FOLDER", "")
    OUTPUTS_FOLDER = os.getenv("OUTPUTS_FOLDER", "")


os.makedirs(UPLOADS_FOLDER, exist_ok=True)
os.makedirs(INPUTS_FOLDER, exist_ok=True)
os.makedirs(OUTPUTS_FOLDER, exist_ok=True)
