import requests
import os
from dotenv import load_dotenv

# load environment file
load_dotenv()


def get_remote_api_key():
    return os.getenv("REMOTE_API_KEY")


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
            return {"ERROR": "invalid request type"}, False
    except requests.exceptions.Timeout:
        return {"ERROR": "timed out"}, False
    if response.status_code == 200 or response.status_code == 201:
        if type == "get" or type == "post":
            return response.json(), True
        elif type == "delete":
            return True, True
        else:
            return None, False
    else:
        return {"ERROR": str(response.content)}, False


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
