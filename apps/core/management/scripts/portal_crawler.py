import uuid
import requests
from bs4 import BeautifulSoup as bs

from django.contrib.auth import get_user_model
from django.utils import timezone
from fake_useragent import UserAgent
from tqdm import tqdm

from apps.core.models import Article
from apps.user.models import UserProfile
from ara.settings import PORTAL_ID, PORTAL_PASSWORD

LOGIN_INFO_SSO2 = {
    'userid': PORTAL_ID,
    'password': PORTAL_PASSWORD,
    'saveid': 'on',
    'phase': 'pass1',
}


LOGIN_INFO_SSO = {
    'userid': PORTAL_ID,
    'password': PORTAL_PASSWORD,
    'saveid': 'on',
    'phase': 'pass2',
}


BASE_URL = 'https://portal.kaist.ac.kr'


def _login_kaist_portal():
    session = requests.Session()
    user_agent = UserAgent()
    login_req1 = session.post('https://portalsso.kaist.ac.kr/ssoProcess2.ps', data=LOGIN_INFO_SSO2,
                              headers={
                                  'User-Agent': user_agent.random,
                              })
    login_req2 = session.post('https://portalsso.kaist.ac.kr/ssoProcess.ps', data=LOGIN_INFO_SSO,
                              headers={
                                  'User-Agent': user_agent.random,
                              })

    print(f'sso2: {login_req1.status_code} & sso: {login_req2.status_code}')

    return session


def _get_article(url, session):
    article_req = session.get(url)
    soup = bs(article_req.text, 'lxml')

    writer_target = '작성자(소속)'
    writer = soup.find('th', text=writer_target).findNext('td').select('label')[0].contents[0].strip()

    title = soup.select('table > tbody > tr > td.req_first')[0].contents[0]
    raw = soup.select('table > tbody > tr:nth-child(4) > td')

    html = ''
    for r in raw:
        html += str(r)

    content_text = ' '.join(bs(html, features='html5lib').find_all(text=True))

    return {
        'title': title,
        'content_text': content_text,
        'content': html,
        'writer': writer,
    }


def crawl_hour():
    session = _login_kaist_portal()

    def _get_board_today(page_num):
        today = True
        board_req = session.get(
            f'{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&userAgent=Chrome&isMobile=False&sortColumn=REG_DATIM&sortMethod=DESC')
        soup = bs(board_req.text, 'lxml')
        linklist = []
        links = soup.select('table > tbody > tr > td > a')
        dates = soup.select('table > tbody > tr > td:nth-child(5)')

        if links:
            print('------- portal login success!')
        else:
            print('------- portal login failed!')

        for link, date in zip(links, dates):
            if date.get_text() == str(timezone.datetime.today().date()).replace('-', '.'):
                linklist.append({'link': link.attrs['href'], 'date': date.get_text()})
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

    for link in links:
        link = link['link']
        board_id = link.split('/')[-2]
        num = link.split('/')[-1]
        full_link = f'{BASE_URL}/board/read.brd?cmd=READ&boardId={board_id}&bltnNo={num}&lang_knd=ko'

        info = _get_article(full_link, session)

        # Since it is time ordered, consequent ones have been posted more than 1 hour ago.

        exist = UserProfile.objects.filter(nickname=info['writer'], is_newara=False)
        if exist:
            user = exist.first().user
        else:
            user = get_user_model().objects.create(username=str(uuid.uuid1()), is_active=False)
            user_profile = UserProfile.objects.create(
                is_newara=False,
                user=user,
                nickname=info['writer'],
            )

        a, created = Article.objects.get_or_create(
            url=full_link,
            defaults={
                'parent_board_id': 1,  # 포탈공지 게시판
                'title': info['title'],
                'content': info['content'],
                'content_text': info['content_text'],
                'created_by': user,
            }
        )

        if created:
            print(f'crawled id: {a.id} - {a.title}')


def crawl_all():
    session = _login_kaist_portal()

    def _get_board(page_num):
        board_req = session.get(
            f'{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&sortColumn=REG_DATIM&sortMethod=DESC')
        soup = bs(board_req.text, 'lxml')
        link = []
        titles = soup.select('table > tbody > tr > td > a')
        for title in titles:
            link.append(title.attrs['href'])

        return link

    links = []
    page_num = 1

    while True:
        link = _get_board(page_num)
        if link:
            links.extend(link)
            page_num += 1
        else:
            break

    for link in tqdm(links):
        board_id = link.split('/')[-2]
        num = link.split('/')[-1]
        full_link = f'{BASE_URL}/board/read.brd?cmd=READ&boardId={board_id}&bltnNo={num}&lang_knd=ko'
        info = _get_article(full_link, session)

        exist = UserProfile.objects.filter(nickname=info['writer'], is_newara=False)
        if exist:
            user = exist.first().user
        else:
            user = get_user_model().objects.create(username=str(uuid.uuid1()), is_active=False)
            user_profile = UserProfile.objects.create(
                is_newara=False,
                user=user,
                nickname=info['writer'],
            )

        Article.objects.create(
            parent_board_id=1,  # 포탈공지 게시판
            title=info['title'],
            content=info['content'],
            content_text=info['content_text'],
            created_by=user,
            url=full_link,
        )
