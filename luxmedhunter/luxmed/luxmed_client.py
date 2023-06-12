import os
import random
import uuid

import requests
import yaml

from luxmedhunter.luxmed.luxmed_api import LuxmedApi
from luxmedhunter.luxmed.luxmed_functions import LuxmedFunctions
from luxmedhunter.utils.dir_paths import PROJECT_DIR
from luxmedhunter.utils.logger_custom import default_logger as logger

APP_VERSION = "4.19.0"
CUSTOM_USER_AGENT = f"Patient Portal; {APP_VERSION}; {str(uuid.uuid4())}; Android; {str(random.randint(23, 29))}; {str(uuid.uuid4())}"


class LuxmedClient:
    """Main client to initialize the session with Portal with all the useful requests calls injected"""

    def __init__(self):
        self.config = self._load_config()
        self.session = None
        self.initialize()
        self.api = LuxmedApi(self)
        self.functions = LuxmedFunctions(self)

    @staticmethod
    def _load_config():
        with open(os.path.join(PROJECT_DIR, "config.yaml"), "r", encoding="utf8") as file:
            return yaml.safe_load(file)

    def initialize(self):
        self.session = self._create_session()
        self._get_access_token()
        self._login()

    def _login(self):
        params = {"app": "search", "client": 3, "paymentSupported": "true", "lang": "pl"}
        response = self.session.get(self.config["urls"]["luxmed_login_url"], params=params)

        if response.status_code != 200:
            raise Exception("Unexpected response code, cannot log in")

        logger.info("Successfully logged in!")

    def _get_access_token(self):
        authentication_body = {
            "username": self.config["luxmed"]["email"],
            "password": self.config["luxmed"]["password"],
            "grant_type": "password",
            "account_id": str(uuid.uuid4())[:35],
            "client_id": str(uuid.uuid4())
        }

        response = self.session.post(self.config["urls"]["luxmed_token_url"], data=authentication_body)

        if response.status_code != 200:
            raise Exception("Unexpected response code, cannot get the token")

        self.session.headers.update({"Authorization": response.json()["access_token"]})

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        headers = {
            'Origin': self.config["urls"]["luxmed_base_url"],
            'Content-Type': 'application/json',
            'x-api-client-identifier': 'iPhone',
            'Accept': 'application/json',
            'Custom-User-Agent': CUSTOM_USER_AGENT,
            'User-Agent': 'okhttp/3.11.0',
            'Accept-Language': 'en;q=1.0, en-PL;q=0.9, pl-PL;q=0.8, ru-PL;q=0.7, uk-PL;q=0.6',
            'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5',
        }

        session.headers.update(headers)
        return session
