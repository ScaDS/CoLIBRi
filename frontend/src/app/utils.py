import base64
import logging
import os
from typing import Any

import cv2
import numpy as np
import requests
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

# load environment file
load_dotenv()


def send_request(
    url: str,
    method: str = "get",
    payload: dict = None,
    timeout: float = 100.0,
) -> Any:
    """
    Send HTTP request and return JSON body.
    :param url: Target URL
    :param payload: Data to send (query params for GET, JSON body otherwise)
    :param method: HTTP method (get, post, delete)
    :param timeout: Request timeout in seconds
    :return: True for delete, response JSON (Python object) otherwise
    :raises:
        requests.HTTPError        -> non-2xx response
        requests.Timeout          -> request timed out
        requests.RequestException -> network/other requests errors
        ValueError                -> unsupported method, or response body not valid JSON
    """
    method_lc = method.lower()
    allowed = {"get", "post", "delete"}
    if method_lc not in allowed:
        raise ValueError(f"Unsupported HTTP method: {method}. Allowed: {sorted(allowed)}")

    try:
        kwargs = {"timeout": timeout}
        if method_lc == "get":
            kwargs["params"] = payload
        else:
            kwargs["json"] = payload

        response = requests.request(method, url, **kwargs)
        # Raise for 4xx/5xx
        response.raise_for_status()
        # Successful delete returns true
        if method == "delete":
            return True
        # Successful get and post expect JSON — raise if not valid
        try:
            return response.json()
        except ValueError as e:
            preview = response.text[:100].replace("\n", " ")
            raise ValueError(f"Response is not valid JSON (preview: {preview!r})") from e
    except requests.exceptions.Timeout:
        raise
    except requests.RequestException:
        raise


def send_request_to_database(resource, method="post", payload=None):
    """
    Sends request to database microservice and returns response json.
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param payload: the payload of the request, e.g. json data for saving a drawing
    :param method: post, get, or delete
    :return: json response from endpoint
    """
    url = f'http://{os.getenv("DATABASE_HOST")}{resource}'
    LOGGER.info(f"Request to database host URL: {url}")
    return send_request(url, method=method, payload=payload)


def send_request_to_preprocessor(resource, method="post", payload=None):
    """
    Sends request to preprocessor microservice and returns response json.
    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param payload: the payload of the request, e.g. json data for saving a drawing
    :param method: post, get, or delete
    :return: json response from endpoint
    """
    url = f'http://{os.getenv("PREPROCESSOR_HOST")}{resource}'
    LOGGER.info(f"Request to preprocessor host URL: {url}")
    return send_request(url, method=method, payload=payload)


def send_request_to_llm_backend(resource, method="post", payload=None):
    """
    Sends request to conversational search microservice and returns response json.
    :param resource: the REST resource to be called, normally /chatbot (include leading /)
    :param payload: the payload of the request, for /chatbot this will be the message and technical_drawing_ids
    :param method: for the /chatbot endpoint, this will be post
    :return: json response, for /chatbot this will be the updated messages and technical_drawing_ids
    """
    url = f'http://{os.getenv("CONVSEARCH_HOST")}{resource}'
    LOGGER.info(f"Request to conv-search host URL: {url}")
    return send_request(url, method=method, payload=payload)


def get_drawing_data_for_drawing_ids(drawing_ids):
    """
    Makes a request to the database for each id in the given list to get the drawing data.
    :param drawing_ids: list of drawing ids
    :return: list of responses from /drawing/get/drawing_id resource in database
    """
    data = []
    for drawing_id in drawing_ids:
        drawing_data = send_request_to_database(resource=f"/drawing/get/{drawing_id}", method="get")
        data.append(drawing_data)
    return data


def convert_bytestring_to_cv2(bytestring):
    """
    Converts an image bytestring to a cv2 image.
    :param bytestring: bytestring of an image file
    :return: np array
    """
    bytestring = str(bytestring).replace("b'", "").replace("'", "")
    arr = np.frombuffer(base64.b64decode(bytestring), dtype=np.uint8)
    return rgb_to_grayscale(cv2.imdecode(arr, flags=1))


def rgb_to_grayscale(rgb_image):
    """
    Converts a cv2 RGB image to grayscale.
    :param rgb_image: cv2 RGB image
    """
    gray_img = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
    return gray_img


def convert_b64img_to_html(b64_string, decode=True):
    if decode:
        b64_string = base64.b64decode(b64_string)
    return "data:image/png;base64," + str(b64_string).replace("b'", "").replace("'", "")
