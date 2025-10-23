import base64
import logging
import os

import cv2
import numpy as np
import requests
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

# load environment file
load_dotenv()


def send_request_to(url, content, type="post"):
    """
    Sends request to url and returns response json.
    If return status code is not 200/201, will return dictionary with key "ERROR".

    :param url: url to sent content to
    :param content: content to sent to url
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    try:
        if type == "get":
            response = requests.get(url, json=content, timeout=100)
        elif type == "post":
            response = requests.post(url, json=content, timeout=100)
        elif type == "delete":
            response = requests.delete(url, timeout=100)
        else:
            return {"ERROR": "invalid request type"}
    except requests.exceptions.Timeout:
        return {"ERROR": "timed out"}
    except requests.exceptions.RequestException as e:
        return {"ERROR": str(e)}
    if response.status_code in (200, 201):
        if type in ("get", "post"):
            try:
                return response.json(), True
            except ValueError:
                return {"ERROR": "invalid JSON in response"}
        elif type == "delete":
            return True
        else:
            return None
    else:
        return {"ERROR": f"status {response.status_code}: {response.text}"}


def send_request_to_database(resource, content=None, type="post"):
    """
    Sends request to database microservice and returns response json.

    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = f'http://{os.getenv("DATABASE_HOST")}{resource}'
    LOGGER.info(f"Connect to database host URL: {url}")
    response, is_ok = send_request_to(url, content, type)
    if is_ok:
        return response
    else:
        raise Exception(response)


def send_request_to_preprocessor(resource, content=None, type="post"):
    """
    Sends request to preprocessor microservice and returns response json.

    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = f'http://{os.getenv("PREPROCESSOR_HOST")}{resource}'
    LOGGER.info(f"Connect to preprocessor host URL: {url}")
    return send_request_to(url, content, type)


def send_request_to_llm_backend(resource, content=None, type="post"):
    """
    Sends request to conversational search microservice and returns response json.

    :param resource: the REST resource to be called, normally /chatbot (include leading /)
    :param content: the payload of the request, for /chatbot this will be the message and technical_drawing_ids
    :param type: for the /chatbot endpoint, this will be post
    :return: json response, for /chatbot this will be the updated messages and technical_drawing_ids
    """
    url = f'http://{os.getenv("CONVSEARCH_HOST")}{resource}'
    LOGGER.info(f"Connect to conv-search host URL: {url}")
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
