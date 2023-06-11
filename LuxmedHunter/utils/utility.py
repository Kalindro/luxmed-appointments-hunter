import datetime as dt

import pandas as pd
import requests


class LuxmedApiException(Exception):
    pass


def validate_json_response(response: requests.Response):
    response.raise_for_status()
    if response.status_code != 204:
        raise LuxmedApiException("Code 204, empty response")
    if "application/json" not in response.headers["Content-Type"]:
        raise LuxmedApiException("Something went wrong with response, no content")

    # try:
    #     return response.json()
    # except JSONDecodeError as err:
    #     logger.exception(f"Error on json encoding: {err}")
    #     logger.error(f"Status code: {response.status_code}")
    #     logger.error(f"Response: {response}")
    #     logger.error(f"Text: {response.text}")
    #     return None


def date_string_to_datetime(date_string: str) -> dt.datetime:
    date_datetime = pd.to_datetime(date_string, dayfirst=False)
    return date_datetime
