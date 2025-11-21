import logging
import os

import requests
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

load_dotenv()

def send_request_to(url, content, type="post"):
    """
    Sends request to url and returns response json. 
    If return status code is not 200/201, will return dictionary with key "ERROR".

    :param url: url to sent content to
    :param content: content to sent to url
    :param type: post, get, or delete
    :return: tuple: json response from endpoint, boolean indicating success
    """
    try:
        if type == "get":
            response = requests.get(url, json=content, timeout=100)
        elif type == "post":
            response = requests.post(url, json=content, timeout=100)
        elif type == "delete":
            response = requests.delete(url, timeout=100)
        else:
            return {"ERROR": f"invalid request type '{type}'"}, False
    except requests.exceptions.Timeout:
        return {"ERROR": "timed out"}, False
    except requests.exceptions.RequestException as e:
        return {"ERROR": str(e)}, False
    if response.status_code in (200, 201):
        if type in ("get", "post"):
            try:
                return response.json(), True
            except ValueError:
                return {"ERROR": "invalid JSON in response"}, False
        elif type == "delete":
            return True, True
        else:
            return None, False
    else:
        return {"ERROR": f"status {response.status_code}: {response.text}"}, False


def send_request_to_database(resource, content=None, type="post"):
    """
    Sends request to database microservice and returns response json.
    If return status code is not 200, will return dictionary with key "ERROR".

    :param resource: the REST resource to be called, e.g. /drawing/get/1 (include leading /)
    :param content: the payload of the request, e.g. json data for saving a drawing
    :param type: post, get, or delete
    :return: json response from endpoint
    """
    url = f'http://{os.getenv("DATABASE_HOST")}{resource}'
    LOGGER.info(f"Connect to database host URL: {url}")
    return send_request_to(url, content, type)
