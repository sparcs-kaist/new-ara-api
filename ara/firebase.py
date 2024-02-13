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
        fcm.send(title, body, open_url, topic=topic)
    except Exception as e:
        print(e)


def fcm_notify_user(user, title, body, open_url):
    targets = FCMToken.objects.filter(user=user)
    for i in targets:
        try:
            fcm.send(title, body, open_url, token=i.token)
        except:
            FCMToken.objects.filter(token=i.token).delete()
