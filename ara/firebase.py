from apps.user.models import FCMToken
from ara.fcm import fcm


def fcm_subscrible(FCM_tokens, subs):  # TODO: fix typo
    for sub in subs:
        response = fcm.subscribe_to_topic(FCM_tokens, sub)


def fcm_unsubscrible(FCM_tokens, subs):  # TODO: fix typo
    for sub in subs:
        response = fcm.unsubscribe_from_topic(FCM_tokens, sub)


def fcm_notify_topic(topic, title, body, open_url):
    try:
        fcm_simple(title, body, open_url, topic=topic)
    except Exception as e:
        print(e)


def fcm_notify_user(user, title, body, open_url):
    targets = FCMToken.objects.filter(user=user)
    for i in targets:
        try:
            fcm_simple(title, body, open_url, token=i.token)
        except:
            FCMToken.objects.filter(token=i.token).delete()


def fcm_simple(title="Title", body="Body", open_url="/", **kwargs):
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

    response = fcm.send(message)
    # Response is a message ID string.
