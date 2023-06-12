from abc import ABC, abstractmethod

import requests


class NotificationClient(ABC):

    @abstractmethod
    def send_message(self, api_token, message):
        pass


class PushoverClient(NotificationClient):
    def __init__(self, user_key):
        self.user_key = user_key

    def send_message(self, api_token, message):
        data = {
            "user": self.user_key,
            "token": api_token,
            "message": message
        }
        response = requests.post("https://api.pushover.net/1/messages.json", data=data)
        if response.status_code != 200:
            raise Exception(f"Pushover error: {response.text}")


class PushbulletClient(NotificationClient):
    def send_message(self, api_token, message):
        headers = {
            "Access-Token": api_token,
            "Content-Type": "application/json"
        }
        data = {
            "type": "note",
            "title": "Notification",
            "body": message
        }
        response = requests.post("https://api.pushbullet.com/v2/pushes", headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Pushbullet error: {response.text}")
