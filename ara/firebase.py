from firebase_admin import messaging

from apps.user.models import FCMToken

def fcm_subscrible(FCM_tokens, subs):
    for sub in subs:
        response = messaging.subscribe_to_topic(FCM_tokens, sub)


def fcm_unsubscrible(FCM_tokens, subs):
    for sub in subs:
        response = messaging.unsubscribe_from_topic(FCM_tokens, sub)


def fcm_notify_topic(topic, title, body, open_url):
    return

    try:
        fcm_simple(title, body, open_url, topic=topic)
    except Exception as e:
        print(e)


def fcm_notify_user(user, title, body, open_url):
    ################## Disable FCM ####################
    return

    targets = FCMToken.objects.filter(user=user)
    for i in targets:
        try:
            fcm_simple(title, body, open_url, token=i.token)
        except:
            FCMToken.objects.filter(token=i.token).delete()
    pass


def fcm_simple(title="Title", body="Body", open_url="/", **kwargs):
    # This registration token comes from the client FCM SDKs.
    # See documentation on defining a message payload.

    ################## Disable FCM ####################
    return
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title=title,
                body=body,
                tag=open_url,
                renotify=True,
                icon="/img/icons/ara-pwa-192.png",
                actions=[
                    messaging.WebpushNotificationAction("action_open", "Open"),
                    messaging.WebpushNotificationAction("action_close", "Close"),
                ],
            ),
            # Maybe bug: fcm_options.link is not working
        ),
        data={"action_open_url": open_url},
        **kwargs,
    )

    response = messaging.send(message)
    # Response is a message ID string.
