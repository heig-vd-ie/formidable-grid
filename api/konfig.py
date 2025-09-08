import os


SECRET_KEY = "B0er23j/4yX R~XHH!jmN]LWX/,?Rh"

APP_DOCKER_NAME = os.getenv("APP_DOCKER_NAME")
INPUTS_FOLDER = os.getenv("INPUTS_FOLDER")
OUTPUTS_FOLDER = os.getenv("OUTPUTS_FOLDER")
UPLOADS_FOLDER = os.getenv("UPLOADS_FOLDER")
INPUTS_FOLDER_NATIVE = os.getenv("INPUTS_FOLDER_NATIVE")
OUTPUTS_FOLDER_NATIVE = os.getenv("OUTPUTS_FOLDER_NATIVE")
UPLOADS_FOLDER_NATIVE = os.getenv("UPLOADS_FOLDER_NATIVE")

if (
    not INPUTS_FOLDER_NATIVE
    or not OUTPUTS_FOLDER_NATIVE
    or not UPLOADS_FOLDER_NATIVE
    or not APP_DOCKER_NAME
    or not INPUTS_FOLDER
    or not OUTPUTS_FOLDER
    or not UPLOADS_FOLDER
):
    raise ValueError("One or more required environment variables are not set")


INPUTS_FOLDER_APP = os.path.join(os.path.dirname(__file__), "..", INPUTS_FOLDER_NATIVE)
OUTPUTS_FOLDER_APP = os.path.join(
    os.path.dirname(__file__), "..", OUTPUTS_FOLDER_NATIVE
)
UPLOADS_FOLDER_APP = os.path.join(
    os.path.dirname(__file__), "..", UPLOADS_FOLDER_NATIVE
)
