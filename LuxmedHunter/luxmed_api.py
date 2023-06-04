from __future__ import annotations

import datetime as dt
import typing as tp
from typing import TYPE_CHECKING

from LuxmedHunter.utils.logger_custom import default_logger as logger
from LuxmedHunter.utils.utility import validate_response

if TYPE_CHECKING:
    from LuxmedHunter.luxmed_client import LuxmedClientInit


class LuxmedApi:

    def __init__(self, luxmed_client: LuxmedClientInit):
        self.config = luxmed_client.config
        self.session = luxmed_client.session

    def get_cities_raw(self) -> list:
        print("Retrieving cities from the Luxmed API...")
        return self._base_request("/Dictionary/cities")

    def get_services_raw(self) -> list:
        logger.info("Retrieving services from the Luxmed API...")
        return self._base_request("/Dictionary/serviceVariantsGroups")

    def get_clinics_and_doctors_raw(self, city_id: int, service_id: int) -> list:
        logger.info("Retrieving clinics and doctors from the Luxmed API...")
        return self._base_request(f"/Dictionary/facilitiesAndDoctors?cityId={city_id}&serviceVariantId={service_id}")

    def get_terms_raw(self, city_id: int, service_id: int, lookup_days: int) -> list:
        print("Getting terms for given search parameters...")
        date_from = dt.date.today().strftime("%Y-%m-%d")
        date_to = (dt.date.today() + dt.timedelta(days=lookup_days))

        params = {"cityId": city_id, "serviceVariantId": service_id, "languageId": 11, "searchDateFrom": date_from,
                  "searchDateTo": date_to}

        return self._base_request("/terms/index", params=params)

    def _base_request(self, uri: str, params: tp.Optional[dict] = None) -> list:
        response = self.session.get(f"{self.config['urls']['luxmed_new_portal_reservation_url']}{uri}", params=params)
        validate_response(response)
        return response.json()
