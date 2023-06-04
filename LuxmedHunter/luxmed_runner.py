import os
import random
import shelve
import time

import schedule

from LuxmedHunter.luxmed.luxmed_client import LuxmedClient
from LuxmedHunter.utils.logger_custom import default_logger as logger
from LuxmedHunter.utils.pushover_client import PushoverClient
from utils.dir_paths import PROJECT_DIR


class LuxmedRunner:
    def __init__(self):
        self.luxmed_client = LuxmedClient()
        self.config = self.luxmed_client.config
        self.db_path = os.path.join(PROJECT_DIR, "LuxmedHunter", "db", "sent_notifs.db")

    def work(self):
        delay = self.config["delay"] + random.randint(1, 30)
        schedule.every(delay).seconds.do(self.check)

    def check(self):
        logger.info("Checking new terms for desired settings")
        terms = self.luxmed_client.functions.get_available_terms_translated(self.config["config"]["city_name"],
                                                                            self.config["config"]["service_name"],
                                                                            self.config["config"]["lookup_days"],
                                                                            self.config["config"]["doctor_name"],
                                                                            self.config["config"]["clinic_name"])
        if terms.empty:
            logger.success("Bad luck, no terms available for the desired settings")
            return
        else:
            logger.success("Success, found below terms:")
            print(terms.to_string())
            self.notifications_handle(terms)

    def notifications_handle(self, terms):
        if not self._is_already_known(terms):
            self._add_to_database(terms)
            self._send_notification(terms)
            logger.success("Notification sent!")
        else:
            logger.success("Notification was already sent")

    def _is_already_known(self, new_terms):
        with shelve.open(self.db_path) as db:
            old_terms = db.get("old_terms")

        if old_terms is None:
            return False

        comparison = old_terms.merge(new_terms, indicator=True, how="outer")
        new_rows = comparison[comparison["_merge"] == "right_only"]

        if new_rows.empty:
            return True
        else:
            return False

    def _add_to_database(self, terms):
        with shelve.open(self.db_path) as db:
            db["old_terms"] = terms

    def _send_notification(self, terms):
        pushover_client = PushoverClient(self.config["pushover"]["api_token"], self.config["pushover"]["user_key"])
        message = "Found new appointment for your desired search!"
        pushover_client.send_message(message)


if __name__ == "__main__":
    logger.info("LuxmedHunter started...")
    client = LuxmedRunner()
    initial_check = client.check()
    set_schedule = client.work()
    while True:
        schedule.run_pending()
        time.sleep(5)
