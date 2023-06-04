from __future__ import annotations
import shelve
import time
from typing import TYPE_CHECKING
from utils.dir_paths import PROJECT_DIR
from pandas import DataFrame as df
import os
import datetime as dt
from LuxmedHunter.utils.logger_custom import default_logger as logger
from LuxmedHunter.utils.utility import date_string_to_datetime

if TYPE_CHECKING:
    from LuxmedHunter.luxmed_client import LuxmedClientInit


class LuxmedFunctions:

    def __init__(self, luxmed_client: LuxmedClientInit):
        self.luxmed_api = luxmed_client.api

    def get_cities(self):
        return df(self.luxmed_api.get_cities_raw()).set_index("name")

    def get_services(self):
        result = self.luxmed_api.get_services_raw()
        services = []
        for category in result:
            for service in category["children"]:
                if not service["children"]:
                    services.append({"id": service["id"], "name": service["name"]})
                for subcategory in service["children"]:
                    services.append({"id": subcategory["id"], "name": subcategory["name"]})

        services_sorted = sorted(services, key=lambda i: i["name"])
        return df(services_sorted).set_index("name")

    def get_clinics(self, city_id: int, service_id: int):
        result = self.luxmed_api.get_clinics_and_doctors_raw(city_id, service_id)
        clinics = [clinic for clinic in result["facilities"]]
        clinics_sorted = sorted(clinics, key=lambda i: i["name"])
        return df(clinics_sorted).set_index("name")

    def get_doctors(self, city_id: int, service_id: int, clinic_id: int = None) -> [{}]:
        result = self.luxmed_api.get_clinics_and_doctors_raw(city_id, service_id)
        doctors = [doctor for doctor in result["doctors"]]
        doctors_sorted = sorted(doctors, key=lambda i: i["firstName"])
        if clinic_id:
            doctors_sorted = [doctor for doctor in doctors_sorted if clinic_id in doctor["facilityGroupIds"]]
        doctors_df = df(doctors_sorted)
        return doctors_df.reindex(
            columns=["firstName", "lastName", "id", "academicTitle", "facilityGroupIds", "isEnglishSpeaker"])

    def get_available_terms(self, city_id: int, service_id: int, lookup_days: int, doctor_id: int = None,
                            clinic_id: int = None):
        result = self.luxmed_api.get_terms_raw(city_id, service_id, lookup_days, clinic_id, doctor_id)
        available_days = result["termsForService"]["termsForDays"]
        if not available_days:
            logger.success("No available terms in the desired date range")

        terms_list = [terms for day in available_days for terms in day["terms"]]
        ultimate_terms_list = []
        for term in terms_list:
            mlem = {
                "day": date_string_to_datetime(term["dateTimeFrom"]).date(),
                "doctor_name": f"{term['doctor']['firstName']} {term['doctor']['lastName']}",
                "doctor_id": term["doctor"]["id"],
                "clinicId": term["clinicId"],
                "serviceId": term["serviceId"],
                "dateTimeFrom": date_string_to_datetime(term["dateTimeFrom"])
            }
            ultimate_terms_list.append(mlem)

        return df(ultimate_terms_list).set_index("day")

    def get_available_terms_translated(self, city_name: str, service_name: str, lookup_days: int,
                                       doctor_name: str = None, clinic_name: str = None):
        db_path = os.path.join(PROJECT_DIR, "LuxmedHunter", "db", "saved_data.db")
        with shelve.open(db_path) as db:
            db_last_update_date = db.get("last_update_date")
            if db_last_update_date is None or dt.date.today() > db_last_update_date:
                db["cities_df"] = self.get_cities()
                time.sleep(5)
                db["services_df"] = self.get_services()
                time.sleep(5)
                db["last_update_date"] = dt.date.today()

            cities_df = db["cities_df"]
            services_df = db["services_df"]

        city_id = cities_df.loc[city_name, "id"]
        service_id = services_df.loc[service_name, "id"]

        self.get_available_terms()
