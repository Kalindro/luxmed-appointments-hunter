from __future__ import annotations

from typing import TYPE_CHECKING

from pandas import DataFrame as df

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

    def get_available_terms(self, city_id: int, service_id: int, lookup_days: int, clinic_id: int = None,
                            doctor_id: int = None):
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

        terms_df = df(ultimate_terms_list).set_index("day")
        print(terms_df.to_string())

        available_terms = [__parse_terms_for_day(terms_per_day) for terms_per_day in result]
        filtered_terms_by_dates = __filter_terms_by_dates(available_terms, from_date, to_date)
        return __filter_terms_by_criteria(filtered_terms_by_dates, part_of_day, clinic_id, doctor_id)

    def __parse_terms_for_day(self, terms_in_current_day: {}) -> {}:
        term_date = utils.convert_string_to_date(terms_in_current_day["day"])
        current_day_terms = [__parse_term_for_day(current_term) for current_term in terms_in_current_day["terms"]]
        return {
            "date": term_date,
            "visits": current_day_terms
        }

    def __parse_term_for_day(self, current_term: {}) -> {}:
        term_time = utils.convert_string_to_time(current_term["dateTimeFrom"])
        doctor_details = current_term["doctor"]
        doctor_name = __parse_doctor_name(doctor_details)
        return {
            "time": term_time,
            "doctor_id": doctor_details["id"],
            "doctor_name": doctor_name,
            "clinic_id": current_term["clinicId"],
            "clinic_name": current_term["clinic"],
            "part_of_day": current_term["partOfDay"]
        }

    def __parse_doctor_name(self, doctor_details: {}) -> str:
        return " ".join(
            filter(None, [doctor_details["academicTitle"], doctor_details["firstName"], doctor_details["lastName"]])
        )

    def __filter_terms_by_dates(self, terms: [{}], from_date: datetime, to_date: datetime) -> [{}]:
        return list(filter(lambda term: from_date <= term["date"] <= to_date, terms))

    def __filter_terms_by_criteria(self, terms: [], part_of_day: int, clinic_id: int = None,
                                   doctor_id: int = None) -> []:
        terms_filters = __get_term_filters_definitions(clinic_id, doctor_id, part_of_day)

        filtered_terms = []
        for term in terms:
            filtered_terms_for_day = list(
                filter(lambda given_term: all([term_filter(given_term) for term_filter in terms_filters]),
                       term["visits"])
            )
            if filtered_terms_for_day:
                filtered_terms.append({"date": term["date"], "visits": filtered_terms_for_day})
        return filtered_terms

    def __get_term_filters_definitions(self, clinic_id: int, doctor_id: int, part_of_day: int) -> [Callable[[Any],
    Union[bool, Any]]]:
        return [
            lambda term: term["part_of_day"] == part_of_day if part_of_day != 0 else term,
            lambda term: term["clinic_id"] == clinic_id if clinic_id else term,
            lambda term: term["doctor_id"] == doctor_id if doctor_id else term
        ]
