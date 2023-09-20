import os
import random
import shelve
import time

import pandas as pd
import schedule
from dotenv import load_dotenv

from luxmedhunter.luxmed.luxmed_client import LuxmedClient
from luxmedhunter.utils.dir_paths import PROJECT_DIR
from luxmedhunter.utils.logger_custom import LoggerCustom, default_logger as logger
from luxmedhunter.utils.pushover_client import PushbulletClient
from luxmedhunter.utils.utility import LuxmedTechnicalException, LuxmedUnauthorizedException

load_dotenv()
LoggerCustom().info_level()


class LuxmedRunner:

    def __init__(self):
        self.luxmed_client = LuxmedClient()
        self.config = self.luxmed_client.config
        self.notifs_db_path = os.path.join(PROJECT_DIR, "luxmedhunter", "db", "sent_notifs.db")

    def check(self):
        time.sleep(random.randint(2, 10))
        logger.info("Checking available appointments for desired settings")
        available_terms = self.luxmed_client.functions.get_available_terms_translated(os.getenv("CITY_NAME"),
                                                                                      os.getenv("SERVICE_NAME"),
                                                                                      int(os.getenv("LOOKUP_DAYS")),
                                                                                      os.getenv("DOCTOR_NAME"),
                                                                                      os.getenv("CLINIC_NAME"))
        if available_terms.empty:
            logger.success("Bad luck, no appointments available for the desired settings")
            self._clear_database()
            return
        else:
            logger.success(f"Success, found below appointments:\n{available_terms.to_string()}")
            self._notifications_handle(available_terms)

    def _notifications_handle(self, available_terms: pd.DataFrame):
        new_terms = self._extract_new_terms(available_terms)
        if not new_terms.empty:
            self._add_to_database(new_terms)
            self._send_notification(new_terms)
            logger.success("Notification sent!")
        else:
            logger.success("Notification was already sent")

    def _extract_new_terms(self, available_terms: pd.DataFrame) -> pd.DataFrame:
        with shelve.open(self.notifs_db_path) as db:
            old_terms = db.get("old_terms")

        if old_terms is None or old_terms.empty:
            return available_terms
        else:
            return available_terms.merge(old_terms, indicator=True, how="left").loc[
                lambda x: x["_merge"] == "left_only"].drop("_merge", axis=1)

    def _clear_database(self):
        with shelve.open(self.notifs_db_path) as db:
            db["old_terms"] = None

    def _add_to_database(self, unseen_terms: pd.DataFrame):
        with shelve.open(self.notifs_db_path) as db:
            old_terms = db["old_terms"]
            db["old_terms"] = pd.concat([old_terms, unseen_terms])

    @staticmethod
    def _send_notification(terms: pd.DataFrame):
        notification_client = PushbulletClient()
        row_messages = []
        for index, row in terms.iterrows():
            date_time_from = row['dateTimeFrom']
            doctor_name = row['doctor_name']
            row_message = f"New appoint: {date_time_from} - {doctor_name}"
            row_messages.append(row_message)

        message = "\n".join(row_messages)
        notification_client.send_message(os.getenv("PUSHBULLET_API_TOKEN"), message)


if __name__ == "__main__":
    interval = 25


    def start_schedule():
        logger.info("Starting fresh schedule...")
        client = LuxmedRunner()
        client.check()  # Initial check
        schedule.every(interval).seconds.do(client.check)


    tries = 0
    while tries <= 4:
        try:
            if schedule.get_jobs():
                schedule.run_pending()
                time.sleep(5)
                tries = 0
            else:
                start_schedule()
        except Exception as err:
            if isinstance(err, LuxmedTechnicalException):
                logger.warning(f"Error: {err}, sleeping for longer")
                time.sleep(1800)
                tries = 0
            elif isinstance(err, LuxmedUnauthorizedException):
                logger.warning(f"Error: {err}, will login again")
                time.sleep(interval)
                tries += 1
            else:
                logger.exception(f"Error, will wait and try to reconnect:\n{err}")
                time.sleep(interval)
                tries += 1

            logger.info(f"Reconnect number: {tries}")

            if tries == 4:
                logger.info("Last try, sleeping longer")
                time.sleep(1800)

            schedule.clear()

    logger.exception(f"There is an constant error, hopefully you weren't banned, goodnight and good luck,"
                     f" sent shutdown notification to Pushbullet")
    message = "LuxmedHunter app has shut down, there were constant errors!"
    PushbulletClient().send_message(os.getenv("PUSHBULLET_API_TOKEN"), message)
