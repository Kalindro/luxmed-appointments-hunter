import os
import random
import uuid
import os
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
    LUXMED_EMAIL = os.getenv("LUXMED_EMAIL")
    LUXMED_PASSWORD = os.getenv("LUXMED_PASSWORD")

    def __init__(self):
        self.config = self._load_config()
        self.session = None
        self.initialize()
        self.api = LuxmedApi(self)
        self.functions = LuxmedFunctions(self)

    def initialize(self):
        if self.LUXMED_EMAIL is None or self.LUXMED_PASSWORD is None:
            raise Exception("Please provide password and/or email, currently it's None")
        self.session = self._create_session()
        self._get_access_token()
        self._login()

    @staticmethod
    def _load_config():
        logger.info(os.listdir(os.path.join(PROJECT_DIR, "config.yaml")))
        with open(os.path.join(PROJECT_DIR, "config.yaml"), "r", encoding="utf8") as file:
            return yaml.safe_load(file)

    def _login(self):
        params = {"app": "search", "client": 3, "paymentSupported": "true", "lang": "pl"}
        response = self.session.get(self.config["urls"]["luxmed_login_url"], params=params)

        if response.status_code != 200:
            raise Exception("Unexpected response code, cannot log in:\n{response.text}")

        logger.info("Successfully logged in!")

    def _get_access_token(self):
        authentication_body = {
            "username": self.LUXMED_EMAIL,
            "password": self.LUXMED_PASSWORD,
            "grant_type": "password",
            "account_id": str(uuid.uuid4())[:35],
            "client_id": str(uuid.uuid4())
        }

        response = self.session.post(self.config["urls"]["luxmed_token_url"], data=authentication_body)

        if response.status_code != 200:
            raise Exception(f"Unexpected response code, cannot get the token:\n{response.text}")

        self.session.headers.update({"Authorization": response.json()["access_token"]})

        logger.info("Successfully got token!")

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        headers = {
            'Origin': self.config["urls"]["luxmed_base_url"],
            'Content-Type': 'application/json',
            'x-api-client-identifier': 'iPhone',
            'Accept': 'application/json',
            'Custom-User-Agent': CUSTOM_USER_AGENT,
            'User-Agent': 'okhttp/3.11.0',
            'Accept-Language': 'en;q=1.0, en-PL;q=0.9, pl-PL;q=0.8',
            'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5',
        }

        session.headers.update(headers)
        return session
