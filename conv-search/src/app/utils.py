import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv

LOGGER = logging.getLogger(__name__)

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
        except requests.exceptions.JSONDecodeError as e:
            preview = response.text[:100].replace("\n", " ")
            raise requests.exceptions.JSONDecodeError(f"Response is not valid JSON - preview: {preview!r})") from e
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
    LOGGER.info(f"Connect to database host URL: {url}")
    return send_request(url, method=method, payload=payload)
