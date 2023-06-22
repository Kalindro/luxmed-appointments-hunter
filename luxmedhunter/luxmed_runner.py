import os
import random
import shelve
import time

import pandas as pd
import schedule
from pandas import DataFrame as df

from luxmedhunter.luxmed.luxmed_client import LuxmedClient
from luxmedhunter.utils.dir_paths import PROJECT_DIR
from luxmedhunter.utils.logger_custom import LoggerCustom, default_logger as logger
from luxmedhunter.utils.pushover_client import PushbulletClient
from luxmedhunter.utils.utility import LuxmedTechnicalException

LoggerCustom().info_level()


class LuxmedRunner:

    def __init__(self):
        self.luxmed_client = LuxmedClient()
        self.config = self.luxmed_client.config
        self.notifs_db_path = os.path.join(PROJECT_DIR, "luxmedhunter", "db", "sent_notifs.db")

    def check(self):
        time.sleep(random.randint(1, 10))
        logger.info("Checking available appointments for desired settings")
        terms = self.luxmed_client.functions.get_available_terms_translated(os.getenv("CITY_NAME"),
                                                                            os.getenv("SERVICE_NAME"),
                                                                            int(os.getenv("LOOKUP_DAYS")),
                                                                            os.getenv("DOCTOR_NAME"),
                                                                            os.getenv("CLINIC_NAME"))
        if terms.empty:
            logger.success("Bad luck, no appointments available for the desired settings")
            return
        else:
            logger.success(f"Success, found below appointments:\n{terms.to_string()}")
            self._notifications_handle(terms)

    def _notifications_handle(self, terms: pd.DataFrame):
        unseen_appointments = self._extract_unseen_terms(terms)
        if not unseen_appointments.empty:
            self._add_to_database(unseen_appointments)
            self._send_notification(unseen_appointments)
            logger.success("Notification sent!")
        else:
            logger.success("Notification was already sent")

    def _extract_unseen_terms(self, new_terms: pd.DataFrame) -> pd.DataFrame:
        with shelve.open(self.notifs_db_path) as db:
            old_terms = db.get("old_terms")

        if old_terms is None:
            old_terms = df()

        return new_terms.merge(old_terms, indicator=True, how="left").loc[lambda x: x["_merge"] == "left_only"].drop(
            "_merge", axis=1)

    def _add_to_database(self, terms: pd.DataFrame):
        with shelve.open(self.notifs_db_path) as db:
            db["old_terms"] = terms

    @staticmethod
    def _send_notification(terms: pd.DataFrame):
        notification_client = PushbulletClient()
        row_messages = []
        for index, row in terms.iterrows():
            date_time_from = row['dateTimeFrom']
            doctor_name = row['doctor_name']
            row_message = f"Hurry! New appointment: {date_time_from} - {doctor_name}"
            row_messages.append(row_message)

        message = "\n".join(row_messages)
        notification_client.send_message(message=message, api_token=os.getenv("PUSHBULLET_API_TOKEN"))


if __name__ == "__main__":
    def start_schedule():
        client = LuxmedRunner()
        client.check()  # Initial check
        schedule.every(60).seconds.do(client.check)


    logger.info("LuxmedHunter started...")

    tries = 0
    while tries < 10:
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
                time.sleep(900)
                tries = 0
            else:
                logger.exception(f"Error, will wait and try to reconnect:\n{err}")
                time.sleep(60)
                tries += 1
                logger.info(f"Reconnect number: {tries}")
                schedule.clear()

    logger.exception(f"There is an constant error, hopefully you weren't banned, goodnight and good luck")
