import os
from flask import request, session
from konfig import UPLOADS_FOLDER_APP
from parser.glm_folders import list_cache_files, load_cache_data
from parser.glm_res import get_node_details, get_link_details, get_simulation_results


def handles_file():
    if request.method == "POST":
        # Handle CSV file upload for fixed nodes
        if (
            ("fixedNodes" in request.files)
            and request.files["fixedNodes"]
            and request.files["fixedNodes"].filename
            and (
                request.files["fixedNodes"].filename.rsplit(".", 1)[-1].lower() == "csv"
            )
        ):
            session["csv"] = 1
            fullfilename = os.path.join(UPLOADS_FOLDER_APP, "curr.csv")
            request.files["fixedNodes"].save(fullfilename)

        # Handle GLM file upload
        if (
            ("glm_file" in request.files)
            and request.files["glm_file"]
            and request.files["glm_file"].filename
            and (request.files["glm_file"].filename.rsplit(".", 1)[1] == "glm")
        ):
            session.clear()
            session["glm_name"] = request.files["glm_file"].filename
            fullfilename = os.path.join(UPLOADS_FOLDER_APP, "curr.glm")
            request.files["glm_file"].save(fullfilename)
