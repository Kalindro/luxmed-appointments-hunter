import os
import random
import uuid

import requests
import yaml

from LuxmedHunter.luxmed_api import LuxmedApi
from LuxmedHunter.luxmed_functions import LuxmedFunctions
from LuxmedHunter.utils.dir_paths import PROJECT_DIR
from LuxmedHunter.utils.logger_custom import LoggerCustom
from LuxmedHunter.utils.utility import validate_response

logger = LoggerCustom().info_only()

APP_VERSION = "4.19.0"
CUSTOM_USER_AGENT = f"Patient Portal; {APP_VERSION}; {str(uuid.uuid4())}; Android; {str(random.randint(23, 29))}; {str(uuid.uuid4())}"


class LuxmedClientInit:

    def __init__(self):
        self.config = self._load_config()
        self.session = self._create_session()
        self._get_access_token()
        self._login()
        self.api = LuxmedApi(self)
        self.functions = LuxmedFunctions(self)

    @staticmethod
    def _load_config():
        with open(os.path.join(PROJECT_DIR, "config.yaml"), "r") as file:
            return yaml.safe_load(file)

    def _login(self):
        params = {
            "app": "search",
            "client": 3,
            "paymentSupported": "true",
            "lang": "pl"
        }
        response = self.session.get(self.config["urls"]["luxmed_login_url"], params=params)
        validate_response(response)
        logger.info("Successfully logged in!")

    def _get_access_token(self):
        authentication_body = {
            "username": self.config["luxmed"]["email"],
            "password": self.config["luxmed"]["password"], "grant_type": "password",
            "account_id": str(uuid.uuid4())[:35], "client_id": str(uuid.uuid4())
        }

        response = self.session.post(self.config["urls"]["luxmed_token_url"], data=authentication_body)
        self.session.headers.update({"Authorization": response.json()["access_token"]})

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        headers = {
            'Origin': self.config["urls"]["luxmed_base_url"],
            'Content-Type': 'application/x-www-form-urlencoded', 'x-api-client-identifier': 'Android',
            'Accept': 'application/json, text/plain, */*', 'Custom-User-Agent': CUSTOM_USER_AGENT,
            'User-Agent': 'okhttp/3.11.0',
            'Accept-Language': 'en;q=1.0, en-PL;q=0.9, pl-PL;q=0.8, ru-PL;q=0.7, uk-PL;q=0.6',
            'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5'
        }
        session.headers.update(headers)
        return session


if __name__ == "__main__":
    client = LuxmedClientInit()
    request = client.functions.get_available_terms_translated(city_name="Warszawa", lookup_days=14,
                                                              service_name="Stomatolog")
