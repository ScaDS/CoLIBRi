import base64
import os

import cv2
import numpy as np
import requests
from dotenv import load_dotenv

# load environment file
load_dotenv()


def send_request_to(url, content, type="post"):
    """
    Sends request to url and returns response json. If return status code is not 200, will return dictionary with key
    "ERROR".
    :param url: url to sent content to
    :param content: content to sent to url
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    try:
        if type == "get":
            response = requests.get(url, json=content, timeout=100)  # timeout of 100 seconds
        elif type == "post":
            response = requests.post(url, json=content, timeout=100)
        elif type == "delete":
            response = requests.delete(url, timeout=100)
        else:
            return {"ERROR": "invalid request type"}
    except requests.exceptions.Timeout:
        return {"ERROR": "timed out"}
    if response.status_code == 200 or response.status_code == 201:
        if type == "get" or type == "post":
            return response.json()
        elif type == "delete":
            return True
        else:
            return None
    else:
        return {"ERROR": str(response.content)}


def send_request_to_database(resource, content=None, type="post"):
    """
    Sends request database resource and returns response json. If return status code is not 200, will return dictionary
    with key "ERROR".
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    # url = "http://database-application:" + os.getenv("DB_PORT_INTERNAL") + resource  # use the container port
    url = "http://172.26.44.37:7101" + resource  # use the container port
    return send_request_to(url, content, type)


def send_request_to_preprocessor(resource, content=None, type="post"):
    """
    Sends request preprocessor resource and returns response json. If return status code is not 200, will return
    dictionary with key "ERROR".
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = "http://preprocessor:" + os.getenv("PP_PORT") + resource
    # url = "http://172.26.44.37:6101" + resource
    # url = "http://0.0.0.0:6001" + resource
    return send_request_to(url, content, type)


def send_request_to_llm_backend(resource, content=None, type="post"):
    """
    Sends request to llm backend and returns response json.
    :param resource: the REST resource to be called, normally /chatbot (include leading /)
    :param content: the payload of the request, for /chatbot this will be the message and technical_drawing_ids
    :param type: for the /chatbot endpoint, this will be post
    :return: json response, for /chatbot this will be the updated messages and technical_drawing_ids
    """
    # url = "http://conv-search:" + os.getenv("CS_PORT") + resource  # url and port of the flask llm backend
    url = "http://172.26.44.37:9101" + resource  # url and port of the flask llm backend
    # url = "http://127.0.0.1:5000" + resource  # url and port of the flask llm backend
    return send_request_to(url, content, type)


def send_request_to_database_updater(resource, content=None, type="post"):
    """
    Sends request database-updater resource and returns response json. If return status code is not 200, will return
    dictionary with key "ERROR".
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = "http://database-updater:" + os.getenv("DBUP_PORT") + resource
    return send_request_to(url, content, type)


def get_drawing_data_for_drawing_ids(drawing_ids):
    """
    Makes a request to the database for each id in the given list to get the drawing data.
    Args:
        drawing_ids: list of drawing_ids

    Returns: a list of responses for the /drawing/get/drawing_id endpoint in database

    """
    data = []
    for drawing_id in drawing_ids:
        drawing_data = send_request_to_database(f"/drawing/get/{drawing_id}", type="get")
        data.append(drawing_data)
    return data


def remove_dupes_from_list(data_list):
    """
    Removes duplicates from the list
    """
    return list(dict.fromkeys(data_list))


def convert_b64img_to_html(b64_string, decode=True):
    if decode:
        b64_string = base64.b64decode(b64_string)
    return "data:image/png;base64," + str(b64_string).replace("b'", "").replace("'", "")


def rgb_to_grayscale(rgb_image):
    """
    Converts a cv2 RGB image to grayscale.
    """
    gray_img = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    return gray_img


def convert_bytestring_to_cv2(bytestring):
    """
    Converts an image bytestring to a cv2 image
    :param bytestring: bytestring of an image file
    :return: np array
    """
    bytestring = str(bytestring).replace("b'", "").replace("'", "")
    arr = np.frombuffer(base64.b64decode(bytestring), dtype=np.uint8)
    return rgb_to_grayscale(cv2.imdecode(arr, flags=1))
