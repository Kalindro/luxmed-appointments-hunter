import datetime as dt

import pandas as pd
import requests


class LuxmedApiException(Exception):
    pass


def validate_response(response: requests.Response):
    if response.status_code == 503:
        raise LuxmedApiException("Service unavailable, probably Luxmed server is down for maintenance")
    if response.status_code != 200:
        raise LuxmedApiException(response.json())


def date_string_to_datetime(date_string: str) -> dt.datetime:
    date_datetime = pd.to_datetime(date_string, dayfirst=True)
    return date_datetime
