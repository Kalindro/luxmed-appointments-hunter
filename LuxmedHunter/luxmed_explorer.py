from LuxmedHunter.luxmed_client import LuxmedClientInit, validate_response
from LuxmedHunter.utils.logger_custom import LoggerCustom


class LuxmedExplorer:

    def __init__(self, luxmed_client: LuxmedClientInit):
        self.config = luxmed_client.config
        self.session = luxmed_client.session

    def get_cities(self) -> list:
        print("Retrieving cities from the Luxmed API...")
        return self._base_request("/Dictionary/cities")

    def get_clinics_and_doctors(self, city_id: int, service_id: int) -> list:
        logger.info("Retrieving clinics and doctors from the Luxmed API...")
        return self._base_request(f"/Dictionary/facilitiesAndDoctors?cityId={city_id}&serviceVariantId={service_id}")

    def get_services(self):
        logger.info("Retrieving services from the Luxmed API...")
        return self._base_request("/Dictionary/serviceVariantsGroups")

    def _base_request(self, uri: str) -> list:
        response = self.session.get(f"{self.config['urls']['luxmed_new_portal_reservation_url']}{uri}")
        validate_response(response)
        return response.json()


if __name__ == "__main__":
    logger = LoggerCustom().info_only()
    client = LuxmedClientInit()
    explorer = LuxmedExplorer(client).get_cities()
    print(explorer)
