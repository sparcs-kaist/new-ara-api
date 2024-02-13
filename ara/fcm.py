"""
Every function calling messaging API should be mocked
to prevent test run uses API limit
"""
from firebase_admin import messaging


class FCM:
    def subscribe_to_topic(self, tokens, sub):
        print("real: subscribe")
        messaging.subscribe_to_topic(tokens, sub)

    def unsubscribe_from_topic(self, tokens, sub):
        print("real: unsubscribe")
        messaging.unsubscribe_from_topic(tokens, sub)

    def send(self, title="Title", body="Body", open_url="/", **kwargs):
        print("real: send")
        # This registration token comes from the client FCM SDKs.
        # See documentation on defining a message payload.

        message = fcm.Message(
            notification=fcm.Notification(
                title=title,
                body=body,
            ),
            webpush=fcm.WebpushConfig(
                notification=fcm.WebpushNotification(
                    title=title,
                    body=body,
                    tag=open_url,
                    renotify=True,
                    icon="/img/icons/ara-pwa-192.png",
                    actions=[
                        fcm.WebpushNotificationAction("action_open", "Open"),
                        fcm.WebpushNotificationAction("action_close", "Close"),
                    ],
                ),
                # Maybe bug: fcm_options.link is not working
            ),
            data={"action_open_url": open_url},
            **kwargs,
        )

        response = messaging.send(message)
        # Response is a message ID string.

        return response


from collections import defaultdict


class MockFCM(FCM):
    def __init__(self):
        self.journal = []

    def get_params_dict(self, **kwargs):
        args = defaultdict(lambda: None)
        args.update(kwargs)
        return args

    def subscribe_to_topic(self, tokens, sub):
        print("mock: subscribe")
        self.journal.append(
            {
                "name": "subscribe_to_topic",
                "params": self.get_params_dict(tokens=tokens, sub=sub),
            }
        )

    def unsubscribe_from_topic(self, tokens, sub):
        print("mock: unsubscribe")
        self.journal.append(
            {
                "name": "unsubscribe_from_topic",
                "params": self.get_params_dict(tokens=tokens, sub=sub),
            }
        )

    def send(self, title="Title", body="Body", open_url="/", **kwargs):
        print("mock: send")
        self.journal.append(
            {
                "name": "send",
                "params": self.get_params_dict(
                    title=title, body=body, open_url=open_url, **kwargs
                ),
            }
        )

    def call_count(self, name):
        return sum([item["name"] == name for item in self.journal])


import sys

fcm = FCM() if "pytest" not in sys.modules else MockFCM()
