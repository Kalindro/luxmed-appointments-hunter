import os
import random
import shelve
import sys
import time

import pandas as pd
import schedule
from pandas import DataFrame as df

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # To run from terminal

from LuxmedHunter.luxmed.luxmed_client import LuxmedClient
from LuxmedHunter.utils.dir_paths import PROJECT_DIR
from LuxmedHunter.utils.logger_custom import LoggerCustom
from LuxmedHunter.utils.logger_custom import default_logger as logger
from LuxmedHunter.utils.pushover_client import PushoverClient

LoggerCustom().info_level()


class LuxmedRunner:

    def __init__(self):
        self.luxmed_client = LuxmedClient()
        self.config = self.luxmed_client.config
        self.notifs_db_path = os.path.join(PROJECT_DIR, "LuxmedHunter", "db", "sent_notifs.db")

    def work(self):
        delay = self.config["delay"] + random.randint(1, 15)
        schedule.every(delay).seconds.do(self.check)

    def check(self):
        logger.info("Checking available appointments for desired settings")
        terms = self.luxmed_client.functions.get_available_terms_translated(self.config["config"]["city_name"],
                                                                            self.config["config"]["service_name"],
                                                                            self.config["config"]["lookup_days"],
                                                                            self.config["config"]["doctor_name"],
                                                                            self.config["config"]["clinic_name"])
        if terms.empty:
            logger.success("Bad luck, no appointments available for the desired settings")
            return
        else:
            logger.success(f"Success, found below appointments:\n{terms.to_string()}")
            self._notifications_handle(terms)

    def _notifications_handle(self, terms):
        unseen_appointments = self._extract_unseen_appointments_only(terms)
        if not unseen_appointments.empty:
            self._add_to_database(unseen_appointments)
            self._send_notification(unseen_appointments)
            logger.success("Notification sent!")
        else:
            logger.success("Notification was already sent")

    def _extract_unseen_appointments_only(self, new_terms) -> pd.DataFrame:
        with shelve.open(self.notifs_db_path) as db:
            old_terms = db.get("old_terms")

        if old_terms is None:
            old_terms = df()

        comparison = old_terms.merge(new_terms, indicator=True, how="outer")
        unseen_rows = comparison[comparison["_merge"] == "right_only"]

        return unseen_rows

    def _add_to_database(self, terms):
        with shelve.open(self.notifs_db_path) as db:
            db["old_terms"] = terms

    def _send_notification(self, terms):
        pushover_client = PushoverClient(self.config["pushover"]["api_token"], self.config["pushover"]["user_key"])
        row_messages = []
        for index, row in terms.iterrows():
            date_time_from = row['dateTimeFrom']
            doctor_name = row['doctor_name']
            row_message = f"Hurry! New appointment: {date_time_from} - {doctor_name}"
            row_messages.append(row_message)

        message = "\n".join(row_messages)
        pushover_client.send_message(message=message, priority=1)


if __name__ == "__main__":
    logger.info("LuxmedHunter started...")
    client = LuxmedRunner()
    initial_check = client.check()
    set_schedule = client.work()

    tries = 0
    while tries < 3:
        try:
            schedule.run_pending()
            time.sleep(5)
        except Exception as err:
            logger.exception(f"Ups, an error occurred, will wait and try to reconnect:\n{err}")
            time.sleep(180)
            tries += 1
            logger.info(f"Reconnect number: {tries}")
            client.luxmed_client.initialize()

    logger.exception("There is an constant error, hopefully you weren't banned, goodnight and good luck:\n{err}")
