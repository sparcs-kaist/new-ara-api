from datetime import timedelta

from django.utils import timezone
from firebase_admin import messaging

from apps.user.models import FCMToken

FIREBASE_ACTIVE = True

def fcm_notify_comment(user, title, body, open_url):
    targets = FCMToken.objects.filter(user=user)

    # Delete expired tokens
    week_ago = timezone.now().date() - timedelta(days=7)
    FCMToken.objects.filter(user=user).filter(last_activated_at__lte=week_ago).delete()

    for i in targets:
        try:
            fcm_simple(i.token, title, body, open_url)
        except:
            FCMToken.objects.filter(token=i.token).delete()


def fcm_simple(FCM_token, title="Title", body="Body", open_url="/"):
    # Do not send message in test environment
    if not FIREBASE_ACTIVE:
        return

    # This registration token comes from the client FCM SDKs.
    # See documentation on defining a message payload.
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
        token=FCM_token,
    )

    response = messaging.send(message)
    # Response is a message ID string.
