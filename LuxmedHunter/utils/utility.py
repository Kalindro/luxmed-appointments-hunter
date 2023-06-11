import datetime as dt

import pandas as pd
import requests
from requests.exceptions import JSONDecodeError

from LuxmedHunter.utils.logger_custom import default_logger as logger


class LuxmedApiException(Exception):
    pass


def handle_response(response: requests.Response):
    response.raise_for_status()
    try:
        return response.json()
    except JSONDecodeError as err:
        logger.exception(f"Error on json encoding: {err}")
        logger.error(f"Status code: {response.status_code}")
        logger.error(f"Response: {response}")
        return None


def date_string_to_datetime(date_string: str) -> dt.datetime:
    date_datetime = pd.to_datetime(date_string, dayfirst=False)
    return date_datetime
