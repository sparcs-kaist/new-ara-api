import hashlib
import re
import uuid
from datetime import datetime, timedelta

import boto3
import requests
from bs4 import BeautifulSoup as bs
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext
from pytz import timezone as pytz_timezone
from tqdm import tqdm

from apps.core.models import Article
from apps.core.models.portal_view_count import PortalViewCount
from apps.user.models import UserProfile
from ara.log import log
from ara.settings import AWS_S3_BUCKET_NAME, PORTAL_JSESSIONID

COOKIES = {"JSESSIONID": PORTAL_JSESSIONID} # JsessionID 기반 auth

BASE_URL = "https://portal.kaist.ac.kr"

KST = pytz_timezone("Asia/Seoul")
PORTAL_NOTICE_BOARD_ID = 1

#Policy : Image와 Attachment의 경우에는 가져와서 AWS S3에 저장할 수 있으나,
#S3 비용 이슈로 텍스트만 가져옴.

#또한 포탈 공지의 조회수를 업데이트 하지 않음.

#이미지 src임베딩도 session이 있어야 가져올 수 있으므로, html에 넣어도 빈 이미지만 나오는 버그가 있음.

def _login_kaist_portal():
    session = requests.Session()
    response = session.get(
        f"{BASE_URL}/kaist/portal/board/nct/0",
        cookies=COOKIES,
    )
    log.info(f"_login_kaist_portal status code: {response.status_code}")
    return session

#Article api link (JSON 형식의 response)
def _get_article_api_link(article_no):
    full_link = f"{BASE_URL}/wz/api/board/recents/{article_no}"
    return full_link

#Article web link (HTML 형식의 response - 실제 웹에서 보이는 화면)
def _get_article_web_link(article_no):
    full_link = f"{BASE_URL}/kaist/portal/board/nct/0#{article_no}"
    return full_link


def _get_portal_article(url, session):
    def _already_hyperlinked(html):
        soup = bs(html, "lxml")
        tagged_links = []
        for child in soup.descendants:
            name = getattr(child, "name", None)
            if name:
                linked = child.attrs.get("src") or child.attrs.get("href")
                if linked:
                    tagged_links.append(linked)

        return tagged_links

    def _enable_hyperlink(s):
        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex, s)
        links = [x[0] for x in url]

        start_index = 0
        new_string = ""
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


    article_req = session.get(url, cookies=COOKIES)
    res_data = article_req.raise_for_status().json()

    #기존에 있던 계정 DB와 충돌을 피하기 위해 writer를 'KAIST Portal'로 통일하여 지정
    writer = "KAIST Portal"

    created_at_str = res_data["regDt"].strip()
    created_at = (
        datetime.strptime(created_at_str, "%Y.%m.%d %H:%M:%S")
        .astimezone(KST)
        .astimezone(timezone.utc)
    )

    view_count_str = res_data["inqCnt"]
    view_count = int(view_count_str)

    #@Todo : 아래 content parsing logic 손보기

    title = res_data["pstTlt"]

    trs = soup.select("table > tbody > tr")
    html = None

    for tr in trs:
        if len(list(tr.children)) == 3:
            html = tr.find("td").prettify()
            break

    if html is None:
        for tr in trs:
            if len(list(tr.children)) == 2:
                html = tr.find("td").prettify()
                break

    html = _save_portal_image(html, session)
    html = _enable_hyperlink(html)

    if html is None:
        raise RuntimeError(gettext("No content for portal article"))

    content_text = " ".join(bs(html, features="html5lib").find_all(text=True))

    return {
        "title": title,
        "content_text": content_text,
        "content": html,
        "writer": writer,
        "created_at": created_at,
        "view_count": view_count,
    }


def crawl_hour(day=None):
    # parameter에서 default로 바로 today()하면, 캐싱되어서 업데이트가 안됨
    if day is None:
        day = timezone.datetime.today().date()
    log.info(f"crawl_hour running for day {day}")

    session = _login_kaist_portal()

    def _get_board_today(page_num):
        today = True
        board_req = session.get(
            f"{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&userAgent=Chrome&isMobile=False&sortColumn=REG_DATIM&sortMethod=DESC",
            cookies=COOKIES,
        )
        soup = bs(board_req.text, "lxml")
        linklist = []
        links = soup.select("table > tbody > tr > td > a")
        dates = soup.select("table > tbody > tr > td:nth-child(5)")

        if links:
            log.info("------- portal login success!")
        else:
            log.info("------- portal login failed!")

        today_date = str(day).replace("-", ".")
        for link, date in zip(links, dates):
            article_date = date.get_text()
            if article_date > today_date:
                continue
            elif article_date == today_date:
                linklist.append({"link": link.attrs["href"], "date": article_date})
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

    last_portal_article_in_db = (
        Article.objects.filter(
            parent_board_id=PORTAL_NOTICE_BOARD_ID,
        )
        .order_by("-created_at")
        .first()
    )

    new_articles = []
    prev_title = ""

    for link in links:
        full_link = _list_link_to_full_link(link["link"])
        info = _get_portal_article(full_link, session)

        # Since it is time ordered, consequent ones have been posted more than 1 hour ago.

        created_at_utc = info["created_at"].astimezone(timezone.utc)

        if (
            created_at_utc < last_portal_article_in_db.created_at
            or info["title"] == prev_title
        ):
            continue

        user_exist = UserProfile.objects.filter(
            nickname=info["writer"], is_newara=False
        )

        if user_exist:
            user = user_exist.first().user
        else:
            user = get_user_model().objects.create(
                username=str(uuid.uuid1()), is_active=False
            )

            UserProfile.objects.create(
                is_newara=False,
                user=user,
                nickname=info["writer"],
                picture="user_profiles/default_pictures/KAIST-logo.png",
            )

        article = Article(
            parent_board_id=PORTAL_NOTICE_BOARD_ID,
            title=info["title"],
            content=info["content"],
            content_text=info["content_text"],
            created_by=user,
            created_at=created_at_utc,
            url=full_link,
            latest_portal_view_count=info["view_count"],
        )

        new_articles.append(article)

        prev_title = article.title

    # DB의 마지막 포탈글과 방금 크롤링한 글 중 가장 이른 글을 비교
    if not new_articles:
        log.info("no new articles")
        return

    earliest_new_article = new_articles[-1]
    is_same_day = (
        last_portal_article_in_db.created_at.date()
        == earliest_new_article.created_at.date()
    )
    is_same_title = last_portal_article_in_db.title == earliest_new_article.title

    if is_same_day and is_same_title:
        last_portal_article_in_db.created_at = earliest_new_article.created_at
        last_portal_article_in_db.content = earliest_new_article.content
        last_portal_article_in_db.save()
        new_articles.pop()

    created_articles = Article.objects.bulk_create(new_articles)

    new_portal_view_counts = []

    for article in created_articles:
        portal_view_count = PortalViewCount(
            article=article,
            view_count=article.latest_portal_view_count,
        )
        new_portal_view_counts.append(portal_view_count)

    PortalViewCount.objects.bulk_create(new_portal_view_counts)

    for i in range(len(created_articles)):
        log.info(f"crawled article: {created_articles[i].title}")

    log.info(f"created {len(created_articles)} articles")


def list_contains_article(articles, article_info):
    for a in articles:
        if (
            a.title == article_info["title"]
            and a.content_text == article_info["content_text"]
        ):
            return True
    return False


def crawl_all():
    session = _login_kaist_portal()

    def _get_board(page_num):
        board_req = session.get(
            f"{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&sortColumn=REG_DATIM&sortMethod=DESC",
            cookies=COOKIES,
        )
        soup = bs(board_req.text, "lxml")
        link = []
        titles = soup.select("table > tbody > tr > td > a")
        for title in titles:
            link.append(title.attrs["href"])

        return link

    page_num = 1

    while True:
        log.info("page_num:", page_num)
        links = []
        link = _get_board(page_num)
        if link:
            links.extend(link)

            with transaction.atomic():
                for link in tqdm(links):
                    full_link = _list_link_to_full_link(link)
                    info = _get_portal_article(full_link, session)

                    user_exist = UserProfile.objects.filter(
                        nickname=info["writer"], is_newara=False
                    )
                    if user_exist:
                        user = user_exist.first().user
                    else:
                        user = get_user_model().objects.create(
                            username=str(uuid.uuid1()), is_active=False
                        )
                        UserProfile.objects.create(
                            is_newara=False,
                            user=user,
                            nickname=info["writer"],
                            picture="user_profiles/default_pictures/KAIST-logo.png",
                        )

                    a, article_created = Article.objects.get_or_create(
                        parent_board_id=PORTAL_NOTICE_BOARD_ID,  # 포탈공지 게시판
                        title=info["title"],
                        content=info["content"],
                        content_text=info["content_text"],
                        created_by=user,
                        url=full_link,
                    )

                    if article_created:
                        a.created_at = info["created_at"]
                        a.save()

                    log.info(info["view_count"])

                    PortalViewCount.objects.update_or_create(
                        article=a,
                        view_count=info["view_count"],
                    )

            page_num += 1

        else:
            break


if __name__ == "__main__":
    _login_kaist_portal()
