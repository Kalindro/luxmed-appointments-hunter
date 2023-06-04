import requests


class PushoverClient:
    def __init__(self, api_token, user_key):
        self.api_token = api_token
        self.user_key = user_key

    def send_message(self, message):
        data = {"token": self.api_token, "user": self.user_key, "message": message}
        r = requests.post("https://api.pushover.net/1/messages.json", data=data)
        if r.status_code != 200:
            raise Exception("Pushover error: %s" % r.text)
