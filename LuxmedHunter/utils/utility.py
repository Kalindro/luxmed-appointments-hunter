import datetime as dt

import pandas as pd
import requests

from LuxmedHunter.utils.logger_custom import default_logger as logger


class LuxmedApiException(Exception):
    pass


def handle_response(response: requests.Response):
    response.raise_for_status()
    try:
        return response.json()
    except Exception as err:
        logger.error(response.status_code)
        logger.error(response.text)
        logger.error(response)
        logger.exception(f"Error on json encoding: {err}")


def date_string_to_datetime(date_string: str) -> dt.datetime:
    date_datetime = pd.to_datetime(date_string, dayfirst=False)
    return date_datetime
