import re
import uuid
from datetime import datetime

import requests
from bs4 import BeautifulSoup as bs

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext
import pyotp
from tqdm import tqdm

from apps.core.models import Article
from apps.user.models import UserProfile
from ara.settings import PORTAL_ID, PORTAL_PASSWORD, PORTAL_2FA_KEY

LOGIN_INFO_SSO2 = {
    'userid': PORTAL_ID,
    'password': PORTAL_PASSWORD,
    'saveid': 'on',
    'phase': 'pass1',
}


LOGIN_INFO_SSO = {
    'user_id': PORTAL_ID,
    'pw': PORTAL_PASSWORD,
    'login_page': 'L_P_COMMON',
}


BASE_URL = 'https://portal.kaist.ac.kr'


def _make_2fa_token():
    totp = pyotp.TOTP(PORTAL_2FA_KEY)
    return totp.now()


def _login_kaist_portal():
    print(f' >>>>> 2FA Token: {_make_2fa_token()}')
    session = requests.Session()
    init_response = session.get(
        'https://portal.kaist.ac.kr/portal/', allow_redirects=True
    )
    login_param_id = init_response.url.split('=')[-1]

    login_response = session.post(
        'https://iam2.kaist.ac.kr/api/sso/login',
        data={**LOGIN_INFO_SSO, 'param_id': login_param_id,},
    )

    if login_response.status_code == 500:
        # Need 2FA
        login_response = session.post(
            'https://iam2.kaist.ac.kr/api/sso/login',
            data={
                **LOGIN_INFO_SSO,
                'param_id': login_param_id,
                'alrdln': 'T',
                'auth_type_2nd': 'google',
                'otp': _make_2fa_token()
            },
        )
    k_uid = login_response.json()['dataMap']['USER_INFO']['kaist_uid']
    state = login_response.json()['dataMap']['state']

    session.post(
        'https://portal.kaist.ac.kr/statics/redirectUri.jsp',
        data={
            'k_uid': k_uid,
            'state': state,
            'success': 'true',
            'result': login_response.text,
            'user_id': PORTAL_ID,
        },
    )

    return session


def _get_article(url, session):
    def _already_hyperlinked(html):
        soup = bs(html, 'lxml')
        tagged_links = []
        for child in soup.descendants:
            name = getattr(child, 'name', None)
            if name:
                linked = child.attrs.get('src') or child.attrs.get('href')
                if linked:
                    tagged_links.append(linked)

        return tagged_links

    def _enable_hyperlink(s):
        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex, s)
        links = [x[0] for x in url]

        start_index = 0
        new_string = ''
        already_hyperlinked = _already_hyperlinked(s)
        for link in links:
            start = start_index + s[start_index:].find(link)
            end = start + len(link)

            if link in already_hyperlinked:
                new_string += s[start_index:end]
            else:
                new_string += s[start_index:start]
                new_string += f'<a href="{link}">{link}</a>'

            start_index = end

        new_string += s[start_index:]

        return new_string

    article_req = session.get(url)
    soup = bs(article_req.text, 'lxml')

    writer = (
        soup.find('th', text='작성자(소속)')
        .findNext('td')
        .select('label')[0]
        .contents[0]
        .strip()
    )
    created_at_str = (
        soup.find('th', text='작성일(조회수)')
        .findNext('td')
        .contents[0]
        .strip()
        .split('(')[0]
    )
    created_at = timezone.get_current_timezone().localize(
        datetime.strptime(created_at_str, '%Y.%m.%d %H:%M:%S')
    )
    title = soup.select('table > tbody > tr > td.req_first')[0].contents[0]

    trs = soup.select('table > tbody > tr')
    html = None

    for tr in trs:
        if len(list(tr.children)) == 3:
            html = tr.find('td').prettify()
            break

    html = _enable_hyperlink(html)

    if html is None:
        raise RuntimeError(gettext('No content for portal article'))

    content_text = ' '.join(bs(html, features='html5lib').find_all(text=True))

    return {
        'title': title,
        'content_text': content_text,
        'content': html,
        'writer': writer,
        'created_at': created_at,
    }


def crawl_hour(day=None):
    # parameter에서 default로 바로 today()하면, 캐싱되어서 업데이트가 안됨
    if day is None:
        day = timezone.datetime.today().date()

    session = _login_kaist_portal()

    def _get_board_today(page_num):
        today = True
        board_req = session.get(
            f'{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&userAgent=Chrome&isMobile=False&sortColumn=REG_DATIM&sortMethod=DESC'
        )
        soup = bs(board_req.text, 'lxml')
        linklist = []
        links = soup.select('table > tbody > tr > td > a')
        dates = soup.select('table > tbody > tr > td:nth-child(5)')

        if links:
            print('------- portal login success!')
        else:
            print('------- portal login failed!')

        today_date = str(day).replace('-', '.')
        for link, date in zip(links, dates):
            article_date = date.get_text()
            if article_date > today_date:
                continue
            elif article_date == today_date:
                linklist.append({'link': link.attrs['href'], 'date': article_date})
            else:
                today = False
                return linklist, today

        return linklist, today

    links = []
    page_num = 1

    while True:
        today_links, is_today = _get_board_today(page_num)
        links.extend(today_links)
        # Now Date of Post is no longer today!
        if not is_today:
            break

        # Next page
        page_num += 1

    last_portal_article_in_db = Article.objects.filter(
            parent_board_id=1,
        ).order_by('-created_at').first()

    new_articles = []
    prev_title = ''

    for link in links:
        link = link['link']
        board_id = link.split('/')[-2]
        num = link.split('/')[-1]
        full_link = f'{BASE_URL}/board/read.brd?cmd=READ&boardId={board_id}&bltnNo={num}&lang_knd=ko'
        info = _get_article(full_link, session)

        # Since it is time ordered, consequent ones have been posted more than 1 hour ago.

        created_at_utc = info['created_at'].astimezone(timezone.utc)

        if created_at_utc < last_portal_article_in_db.created_at or info['title'] == prev_title:
            continue

        user_exist = UserProfile.objects.filter(nickname=info['writer'], is_newara=False)

        if user_exist:
            user = user_exist.first().user
        else:
            user = get_user_model().objects.create(
                username=str(uuid.uuid1()), is_active=False
            )

            UserProfile.objects.create(
                is_newara=False,
                user=user,
                nickname=info['writer'],
                picture='user_profiles/default_pictures/KAIST-logo.png',
            )

        article = Article(
                    parent_board_id=1,
                    title=info['title'],
                    content=info['content'],
                    content_text=info['content_text'],
                    created_by=user,
                    created_at=created_at_utc,
                    url=full_link
                  )

        new_articles.append(article)
        prev_title = article.title

    # DB의 마지막 포탈글과 방금 크롤링한 글 중 가장 이른 글을 비교
    earliest_new_article = new_articles[-1]
    is_same_day = last_portal_article_in_db.created_at.date() == earliest_new_article.created_at.date()
    is_same_title = last_portal_article_in_db.title == earliest_new_article.title

    if is_same_day and is_same_title:
        last_portal_article_in_db.created_at = earliest_new_article.created_at
        last_portal_article_in_db.content = earliest_new_article.content
        last_portal_article_in_db.save()
        new_articles.pop()

    created_articles = Article.objects.bulk_create(new_articles)

    for i in range(len(created_articles)):
        print(f'crawled article: {created_articles[i].title}')


def list_contains_article(articles, article_info):
    for a in articles:
        if a.title == article_info['title'] and a.content_text == article_info['content_text']:
            return True
    return False


def crawl_all():
    session = _login_kaist_portal()

    def _get_board(page_num):
        board_req = session.get(
            f'{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&sortColumn=REG_DATIM&sortMethod=DESC'
        )
        soup = bs(board_req.text, 'lxml')
        link = []
        titles = soup.select('table > tbody > tr > td > a')
        for title in titles:
            link.append(title.attrs['href'])

        return link

    page_num = 1

    while True:
        print('page_num:', page_num)
        links = []
        link = _get_board(page_num)
        if link:
            links.extend(link)

            with transaction.atomic():
                for link in tqdm(links):
                    board_id = link.split('/')[-2]
                    num = link.split('/')[-1]
                    full_link = f'{BASE_URL}/board/read.brd?cmd=READ&boardId={board_id}&bltnNo={num}&lang_knd=ko'
                    info = _get_article(full_link, session)

                    user_exist = UserProfile.objects.filter(
                        nickname=info['writer'], is_newara=False
                    )
                    if user_exist:
                        user = user_exist.first().user
                    else:
                        user = get_user_model().objects.create(
                            username=str(uuid.uuid1()), is_active=False
                        )
                        user_profile = UserProfile.objects.create(
                            is_newara=False,
                            user=user,
                            nickname=info['writer'],
                            picture='user_profiles/default_pictures/KAIST-logo.png',
                        )

                    a, created = Article.objects.get_or_create(
                        parent_board_id=1,  # 포탈공지 게시판
                        title=info['title'],
                        content=info['content'],
                        content_text=info['content_text'],
                        created_by=user,
                        url=full_link,
                    )

                    if created:
                        a.created_at = info['created_at']
                        a.save()

            page_num += 1

        else:
            break


if __name__ == '__main__':
    _login_kaist_portal()
