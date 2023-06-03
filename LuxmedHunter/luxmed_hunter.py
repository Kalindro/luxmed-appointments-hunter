import datetime
import shelve
from typing import List

from LuxmedHunter.luxmed_client import LuxmedClientInit
from LuxmedHunter.pushover_client import PushoverClient
from LuxmedHunter.utils.logger_custom import LoggerCustom


class LuxmedHunter:

    def __init__(self, luxmed_client: LuxmedClientInit):
        self.config = luxmed_client.config
        self.session = luxmed_client.session

    def check(self):
        appointments = self._get_appointments_new_portal()
        if not appointments:
            logger.info("No appointments found")
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
                logger.info("Notification was already sent.")

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
            (cityId, serviceId, clinicIds, doctorIds) = self.config["luxmedsniper"]["doctor_locator_id"].strip().split(
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

        response = self.session.get(self.config["urls"]["luxmed_new_portal_reservation_url"], params=params)
        return [*filter(lambda a: datetime.datetime.fromisoformat(a['AppointmentDate']).date() <= date_to,
                        self._parse_visits_new_portal(response))]

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


if __name__ == "__main__":
    logger = LoggerCustom().info_only()
    client = LuxmedClientInit()
    hunter = LuxmedHunter(client).test()
