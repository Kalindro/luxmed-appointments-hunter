import requests


class LuxmedApiException(Exception):
    pass


def validate_response(response: requests.Response):
    if response.status_code == 503:
        raise LuxmedApiException("Service unavailable, probably Luxmed server is down for maintenance")
    if response.status_code != 200:
        raise LuxmedApiException(response.json())
