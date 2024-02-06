"""
Every function calling messaging API should be mocked
to prevent test run uses API limit
"""
from firebase_admin import messaging


class FCM:
    Message = messaging.Message
    Notification = messaging.Notification
    WebpushNotificationAction = messaging.WebpushNotificationAction
    WebpushConfig = messaging.WebpushConfig
    WebpushNotification = messaging.WebpushNotification

    def subscribe_to_topic(self, tokens, sub):
        print("real: subscribe")
        messaging.subscribe_to_topic(tokens, sub)

    def unsubscribe_from_topic(self, tokens, sub):
        print("real: unsubscribe")
        messaging.unsubscribe_from_topic(tokens, sub)

    def send(self, message):
        print("real: send")
        messaging.send(message)


class MockFCM(FCM):
    def __init__(self):
        self.journal = []

    def subscribe_to_topic(self, tokens, sub):
        print("mock: subscribe")
        self.journal.append({"name": "subscribe_to_topic", "params": [tokens, sub]})

    def unsubscribe_from_topic(self, tokens, sub):
        print("mock: unsubscribe")
        self.journal.append({"name": "unsubscribe_from_topic", "params": [tokens, sub]})

    def send(self, message):
        print("mock: send")
        self.journal.append({"name": "send", "params": [message]})

    def call_count(self, name):
        return sum([item["name"] == name for item in self.journal])


import sys

fcm = FCM() if "pytest" not in sys.modules else MockFCM()
