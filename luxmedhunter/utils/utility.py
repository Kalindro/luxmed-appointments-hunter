import datetime as dt

import pandas as pd
import requests


class LuxmedApiException(Exception):
    pass


class LuxmedTechnicalException(Exception):
    pass


def validate_json_response(response: requests.Response):
    if response.status_code == 503:
        raise LuxmedTechnicalException("Code 503, Luxmed servers maintenance")
    if response.status_code == 204:
        raise LuxmedApiException("Code 204, empty response")
    if "application/json" not in response.headers["Content-Type"]:
        raise LuxmedApiException("Something went wrong with response, not a JSON")
    response.raise_for_status()


def date_string_to_datetime(date_string: str) -> dt.datetime:
    date_datetime = pd.to_datetime(date_string, dayfirst=False)
    return date_datetime
