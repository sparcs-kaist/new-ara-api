from django.utils import timezone, dateformat
from django.core.mail import send_mail

from apps.core.models import CommunicationArticle, UserProfile
from ara.settings import env


if env('DJANGO_ENV') == 'production':
    django_env = ''
    BASE_URL = 'https://newara.sparcs.org/post'
else:
    django_env = '[DEV]'
    BASE_URL = 'https://newara.dev.sparcs.org/post'


def _get_preparing_articles():
    articles = CommunicationArticle.objects.filter(
        school_response_status=1,
    ).order_by('response_deadline')

    return articles


# 답변일까지 13일, 7일, 1일이 남았을 때 reminder 메일 발송
def _is_remind_day(articles):
    days_left_to_remind = [13, 7, 1]

    for article in articles:
        if article.days_left in days_left_to_remind:
            return True

    return False


def _format_date(date):
    return dateformat.format(date, 'Y-m-d')


def _format_dday(days_left):
    if days_left < 0:
        dday = f'[D+{days_left * -1}]'
    elif days_left == 0:
        dday = '[D-Day]'
    else:
        dday = f'[D-{days_left}]'

    return dday


def _make_title():
    return f"[NewAra]{django_env} {_format_date(timezone.localtime())} '학교에게 전합니다' 답변대기 목록"


def _make_message(articles):
    new_message_list = ""
    old_message_list = ""

    num_new_message = 0
    num_old_message = 0

    for article in articles:
        url = f"{BASE_URL}/{article.article_id}"
        message = f"{_format_dday(article.days_left)} {_format_date(article.response_deadline)} '{article.article.title}' {url}\n"

        if article.days_left == 13:
            new_message_list += message
            num_new_message += 1
        else:
            old_message_list += message
            num_old_message += 1

    new_message_header = f"새로운 답변 대기 목록 {num_new_message}개\n"
    old_message_header = f"\n기존 답변 대기 목록 {num_old_message}개\n"

    return new_message_header + new_message_list + old_message_header + old_message_list


def _get_mailing_list():
    mailing_list = []

    admin_users = UserProfile.objects.filter(
        group=6
    ).values('sso_user_info')

    for user in admin_users:
        mailing_list.append(user['sso_user_info']['email'])

    return mailing_list


def send_email():
    preparing_articles = _get_preparing_articles()

    if not _is_remind_day(preparing_articles):
        return

    title = _make_title()

    message = _make_message(preparing_articles)

    mailing_list = _get_mailing_list()

    send_mail(title, message, 'new-ara@sparcs.org', mailing_list)
