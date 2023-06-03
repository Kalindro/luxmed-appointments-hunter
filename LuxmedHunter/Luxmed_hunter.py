import datetime
import os
import random
import shelve
import uuid
from typing import List

import requests
import yaml

from LuxmedHunter.utils.dir_paths import PROJECT_DIR
from LuxmedHunter.utils.logger_custom import LoggerCustom

logger = LoggerCustom().info_level()

APP_VERSION = "4.19.0"
CUSTOM_USER_AGENT = f"Patient Portal; {APP_VERSION}; {str(uuid.uuid4())}; Android; {str(random.randint(23, 29))}; {str(uuid.uuid4())}"


class LuxmedHunter:
    LUXMED_TOKEN_URL = "https://portalpacjenta.luxmed.pl/PatientPortalMobileAPI/api/token"
    LUXMED_LOGIN_URL = "https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogInToApp"
    NEW_PORTAL_RESERVATION_URL = "https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/terms/index"

    def __init__(self):
        self.config = self._load_config()
        self._create_session()
        self._get_access_token()
        self._login()

    @staticmethod
    def _load_config():
        with open(os.path.join(PROJECT_DIR, "config.yaml"), "r") as file:
            return yaml.safe_load(file)

    def _create_session(self):
        self.session = requests.Session()
        self.session.headers.update({'Host': "portalpacjenta.luxmed.pl"})
        self.session.headers.update({'Origin': "https://portalpacjenta.luxmed.pl"})
        self.session.headers.update({'Content-Type': "application/x-www-form-urlencoded"})
        self.session.headers.update({'x-api-client-identifier': 'iPhone'})
        self.session.headers.update({'Accept': 'application/json, text/plain, */*'})
        self.session.headers.update({'Custom-User-Agent': CUSTOM_USER_AGENT})
        self.session.headers.update({'User-Agent': 'okhttp/3.11.0'})
        self.session.headers.update({'Accept-Language': 'en;q=1.0, en-PL;q=0.9, pl-PL;q=0.8, ru-PL;q=0.7, uk-PL;q=0.6'})
        self.session.headers.update({'Accept-Encoding': 'gzip;q=1.0, compress;q=0.5'})

    def _get_access_token(self) -> str:

        authentication_body = {"username": self.config["luxmed"]["email"],
                               "password": self.config["luxmed"]["password"],
                               "grant_type": "password", "account_id": str(uuid.uuid4())[:35],
                               "client_id": str(uuid.uuid4())}

        response = self.session.post(LuxmedHunter.LUXMED_TOKEN_URL, data=authentication_body)
        content = response.json()
        self.access_token = content["access_token"]
        self.refresh_token = content["refresh_token"]
        self.token_type = content["token_type"]
        self.session.headers.update({"Authorization": self.access_token})

        return response.json()["access_token"]

    def _login(self):
        params = {"app": "search", "client": 3, "paymentSupported": "true", "lang": "pl"}
        response = self.session.get(LuxmedHunter.LUXMED_LOGIN_URL, params=params)

        if response.status_code != 200:
            raise Exception("Unexpected response code, cannot log in")
        logger.info("Successfully logged in!")

    def _parse_visits_new_portal(self, data) -> List[dict]:
        appointments = []
        (clinicIds, doctorIds) = self.config["luxmedsniper"]["doctor_locator_id"].strip().split('*')[-2:]
        content = data.json()
        for termForDay in content["termsForService"]["termsForDays"]:
            for term in termForDay["terms"]:
                doctor = term["doctor"]

                if doctorIds != "-1" and str(doctor["id"]) != doctorIds:
                    continue
                if clinicIds != "-1" and str(term["clinicId"]) != clinicIds:
                    continue

                appointments.append({'AppointmentDate': term['dateTimeFrom'], 'ClinicId': term['clinicId'],
                                     'ClinicPublicName': term['clinic'],
                                     'DoctorName': f'{doctor["academicTitle"]} {doctor["firstName"]} {doctor["lastName"]}',
                                     'ServiceId': term['serviceId']})
        return appointments

    def _get_appointments_new_portal(self):
        try:
            (cityId, serviceId, clinicIds, doctorIds) = self.config['luxmedsniper']['doctor_locator_id'].strip().split(
                '*')
        except ValueError:
            raise Exception('DoctorLocatorID seems to be in invalid format')
        date_to = (datetime.date.today() + datetime.timedelta(days=self.config['luxmedsniper']['lookup_time_days']))
        params = {"cityId": cityId, "serviceVariantId": serviceId, "languageId": 10,
                  "searchDateFrom": datetime.date.today().strftime("%Y-%m-%d"),
                  "searchDateTo": date_to.strftime("%Y-%m-%d"), }
        if clinicIds != '-1':
            params['facilitiesIds'] = clinicIds.split(',')
        if doctorIds != '-1':
            params['doctorsIds'] = doctorIds.split(',')

        response = self.session.get(LuxmedHunter.NEW_PORTAL_RESERVATION_URL, params=params)
        return [*filter(lambda a: datetime.datetime.fromisoformat(a['AppointmentDate']).date() <= date_to,
                        self._parse_visits_new_portal(response))]

    def check(self):
        appointments = self._get_appointments_new_portal()
        if not appointments:
            logger.info("No appointments found.")
            return
        for appointment in appointments:
            logger.info(
                "Appointment found! {AppointmentDate} at {ClinicPublicName} - {DoctorName}".format(**appointment))
            if not self._is_already_known(appointment):
                self._add_to_database(appointment)
                self._send_notification(appointment)
                logger.info(
                    "Notification sent! {AppointmentDate} at {ClinicPublicName} - {DoctorName}".format(**appointment))
            else:
                logger.info('Notification was already sent.')

    def _add_to_database(self, appointment):
        db = shelve.open(self.config['misc']['notifydb'])
        notifications = db.get(appointment['DoctorName'], [])
        notifications.append(appointment['AppointmentDate'])
        db[appointment['DoctorName']] = notifications
        db.close()

    def _is_already_known(self, appointment):
        db = shelve.open(self.config['misc']['notifydb'])
        notifications = db.get(appointment['DoctorName'], [])
        db.close()
        if appointment['AppointmentDate'] in notifications:
            return True
        return False

    def _send_notification(self, appointment):
        pushover_client = PushoverClient(self.config["pushover"]["api_token"], self.config["pushover"]["user_key"])
        pushover_client.send_message(appointment)


class PushoverClient:
    def __init__(self, api_token, user_key):
        self.api_token = api_token
        self.user_key = user_key

    def send_message(self, message):
        data = {"token": self.api_token, "user": self.user_key, "message": message}
        r = requests.post("https://api.pushover.net/1/messages.json", data=data)
        if r.status_code != 200:
            raise Exception("Pushover error: %s" % r.text)


if __name__ == "__main__":
    logger = LoggerCustom().info_only()
    LuxmedHunter()
