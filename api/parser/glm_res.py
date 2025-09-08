import os
import json
from flask import jsonify, request
from api.parser.glm_inp import readGLM
from api.konfig import *


def get_node_details():
    """Get detailed information about a specific node (Advanced Option)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    node_name = data.get("node_name")
    if not node_name:
        return jsonify({"error": "No node name provided"}), 400

    try:
        # Load the current GLM file
        glm_file_path = os.path.join(UPLOADS_FOLDER_APP, "curr.glm")

        if not os.path.isfile(glm_file_path):
            return jsonify({"error": "No GLM file loaded"}), 404

        # Parse the GLM file to get detailed object information
        objs, _, _ = readGLM(glm_file_path)

        # Find the node object(s) with the given name
        node_objects = [obj for obj in objs if obj.get("name") == node_name]

        if not node_objects:
            # Try to find by parent relationship or other name fields
            node_objects = [obj for obj in objs if obj.get("name_oldGLM") == node_name]

        if not node_objects:
            return jsonify({"error": f"Node {node_name} not found"}), 404

        # Get the main node object
        main_node = node_objects[0]

        # Find child objects (like generators, capacitors, etc.)
        child_objects = [obj for obj in objs if obj.get("parent") == node_name]

        # Find connected elements (lines, transformers, etc.)
        connections = []
        link_types = [
            "overhead_line",
            "switch",
            "underground_line",
            "regulator",
            "transformer",
            "triplex_line",
            "fuse",
        ]

        for obj in objs:
            if obj.get("class") in link_types:
                if obj.get("from") == node_name:
                    connections.append(
                        {
                            "name": obj.get("to", "Unknown"),
                            "type": "to",
                            "linkType": obj.get("class"),
                            "object": obj,
                        }
                    )
                elif obj.get("to") == node_name:
                    connections.append(
                        {
                            "name": obj.get("from", "Unknown"),
                            "type": "from",
                            "linkType": obj.get("class"),
                            "object": obj,
                        }
                    )

        # Extract properties from the main node (excluding metadata)
        properties = {}
        excluded_keys = {"name", "class", "startLine", "name_oldGLM", "parent"}

        for key, value in main_node.items():
            if key not in excluded_keys:
                properties[key] = value

        # Add child object properties
        child_properties = {}
        for child in child_objects:
            child_name = child.get("class", "child")
            child_props = {}
            for key, value in child.items():
                if key not in excluded_keys:
                    child_props[key] = value
            if child_props:
                child_properties[child_name] = child_props

        # Prepare response
        response_data = {
            "name": node_name,
            "class": main_node.get("class"),
            "properties": properties if properties else None,
            "child_properties": child_properties if child_properties else None,
            "connections": connections if connections else None,
            "children": (
                [child.get("class") for child in child_objects]
                if child_objects
                else None
            ),
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Error retrieving node details: {str(e)}"}), 500


def get_link_details():
    """Get detailed information about a specific link/line (Advanced Option)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    source_node = data.get("source")
    target_node = data.get("target")
    link_type = data.get("link_type")

    if not source_node or not target_node:
        return jsonify({"error": "Source and target nodes required"}), 400

    try:
        # Load the current GLM file
        glm_file_path = os.path.join(UPLOADS_FOLDER_APP, "curr.glm")

        if not os.path.isfile(glm_file_path):
            return jsonify({"error": "No GLM file loaded"}), 404

        # Parse the GLM file to get detailed object information
        objs, _, _ = readGLM(glm_file_path)

        # Find the link object with the given from/to nodes
        link_objects = []
        for obj in objs:
            if obj.get("class") == link_type and (
                (obj.get("from") == source_node and obj.get("to") == target_node)
                or (obj.get("from") == target_node and obj.get("to") == source_node)
            ):
                link_objects.append(obj)

        if not link_objects:
            return (
                jsonify(
                    {"error": f"Link between {source_node} and {target_node} not found"}
                ),
                404,
            )

        # Get the main link object
        main_link = link_objects[0]

        # Extract properties from the main link (excluding metadata)
        properties = {}
        excluded_keys = {
            "name",
            "class",
            "startLine",
            "name_oldGLM",
            "parent",
            "from",
            "to",
        }

        for key, value in main_link.items():
            if key not in excluded_keys:
                properties[key] = value

        # Prepare response
        response_data = {
            "success": True,
            "name": main_link.get("name", f"{source_node}-{target_node}"),
            "class": main_link.get("class"),
            "from": main_link.get("from"),
            "to": main_link.get("to"),
            "properties": properties if properties else None,
            "type": "link",
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Error retrieving link details: {str(e)}"}), 500


def get_simulation_results():
    """Get simulation results from cache folder (Advanced Option)"""
    try:
        # First try to get results from JSON file (preferred)
        json_files = [f for f in os.listdir(OUTPUTS_FOLDER_APP) if f.endswith(".json")]

        if json_files:
            # Use the first JSON file found
            json_file = os.path.join(OUTPUTS_FOLDER_APP, json_files[0])

            with open(json_file, "r") as f:
                data = json.load(f)

            results = []
            objects = data.get("objects", {})

            for obj_name, obj_data in objects.items():
                if obj_data.get("class") in [
                    "node",
                    "load",
                    "meter",
                    "triplex_meter",
                    "triplex_node",
                ]:
                    # Extract voltage data
                    voltage_A = obj_data.get("voltage_A", "0+0j V")
                    voltage_B = obj_data.get("voltage_B", "0+0j V")
                    voltage_C = obj_data.get("voltage_C", "0+0j V")

                    # Parse complex voltage values
                    def parse_voltage(v_str):
                        if isinstance(v_str, str):
                            # Remove 'V' and parse complex number
                            v_clean = v_str.replace("V", "").strip()
                            if "j" in v_clean:
                                try:
                                    return complex(v_clean.replace("j", "j"))
                                except:
                                    return complex(0)
                            else:
                                try:
                                    return complex(float(v_clean))
                                except:
                                    return complex(0)
                        return complex(0)

                    volt_a = parse_voltage(voltage_A)
                    volt_b = parse_voltage(voltage_B)
                    volt_c = parse_voltage(voltage_C)

                    # Calculate magnitudes
                    mag_a = abs(volt_a)
                    mag_b = abs(volt_b)
                    mag_c = abs(volt_c)

                    # Calculate overall voltage magnitude (max of phases)
                    voltage_magnitude = max(mag_a, mag_b, mag_c)

                    # Get nominal voltage (assuming 2401.78V line-to-neutral)
                    nominal_voltage = 2401.78
                    voltage_percent = (
                        (voltage_magnitude / nominal_voltage) * 100
                        if voltage_magnitude > 0
                        else 0
                    )

                    result_row = {
                        "node": obj_name,
                        "class": obj_data.get("class", ""),
                        "bustype": obj_data.get("bustype", ""),
                        "phases": obj_data.get("phases", ""),
                        "nominal_voltage": nominal_voltage,
                        "voltage_A_mag": mag_a,
                        "voltage_B_mag": mag_b,
                        "voltage_C_mag": mag_c,
                        "voltage_magnitude": voltage_magnitude,
                        "voltage_percent": voltage_percent,
                        "latitude": obj_data.get("latitude", ""),
                        "longitude": obj_data.get("longitude", ""),
                    }
                    results.append(result_row)

            return jsonify(
                {
                    "success": True,
                    "source": "json",
                    "file": json_files[0],
                    "results": results,
                    "total_nodes": len(results),
                }
            )

        else:
            return jsonify({"error": "No simulation results found"}), 404

    except Exception as e:
        return jsonify({"error": f"Error reading simulation results: {str(e)}"}), 500
