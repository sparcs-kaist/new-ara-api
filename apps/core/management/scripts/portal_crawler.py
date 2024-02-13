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
from ara.settings import (
    AWS_S3_BUCKET_NAME,
    PORTAL_ID,
    PORTAL_JSESSIONID,
    PORTAL_PASSWORD,
)

LOGIN_INFO_SSO2 = {
    "userid": PORTAL_ID,
    "password": PORTAL_PASSWORD,
    "saveid": "on",
    "phase": "pass1",
}

LOGIN_INFO_SSO = {
    "user_id": PORTAL_ID,
    "pw": PORTAL_PASSWORD,
    "login_page": "L_P_COMMON",
}

COOKIES = {"JSESSIONID": PORTAL_JSESSIONID}

BASE_URL = "https://portal.kaist.ac.kr"

KST = pytz_timezone("Asia/Seoul")
PORTAL_NOTICE_BOARD_ID = 1


def _login_kaist_portal():
    session = requests.Session()
    response = session.get(
        f"{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page=1&userAgent=Chrome&isMobile=False&sortColumn=REG_DATIM&sortMethod=DESC",
        cookies=COOKIES,
    )
    log.info(f"_login_kaist_portal status code: {response.status_code}")
    return session


def _list_link_to_full_link(link):
    board_id = link.split("/")[-2]
    num = link.split("/")[-1]
    full_link = f"{BASE_URL}/board/read.brd?cmd=READ&boardId={board_id}&bltnNo={num}&lang_knd=ko"
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

    def _get_new_url_and_save_to_s3(url, session):
        if url.startswith("data:") or "." in url.split("/")[-1]:  # not a portal image
            return url

        if url.startswith("/board"):
            return f"https://{BASE_URL}/${url}"

        enc = hashlib.md5()
        enc.update(url.encode())
        hash = enc.hexdigest()[:20]
        filename = f'files/portal_image_{hash}.{url.split("_")[-1]}'

        if url.startswith("/board"):
            url = str(BASE_URL) + url

        r = session.get(url, stream=True, cookies=COOKIES)
        if r.status_code == 200:
            s3 = boto3.client("s3")
            s3.upload_fileobj(r.raw, Bucket=AWS_S3_BUCKET_NAME, Key=filename)

        return f"https://{AWS_S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"

    def _save_portal_image(html, session):
        soup = bs(html, "lxml")
        for child in soup.find_all("img", {}):
            old_url = child.attrs.get("src")
            try:
                new_url = _get_new_url_and_save_to_s3(old_url, session)
                child["src"] = new_url
            except Exception as exc:
                log.info(child)
                raise exec

        return str(soup)

    article_req = session.get(url, cookies=COOKIES)
    soup = bs(article_req.text, "lxml")

    writer = (
        soup.find("th", text="작성자(소속)")
        .findNext("td")
        .select("label")[0]
        .contents[0]
        .strip()
    )

    created_at_view_count_str = (
        soup.find("th", text="작성일(조회수)").findNext("td").contents[0].strip()
    )

    created_at_str = created_at_view_count_str.split("(")[0]
    created_at = (
        datetime.strptime(created_at_str, "%Y.%m.%d %H:%M:%S")
        .astimezone(KST)
        .astimezone(timezone.utc)
    )

    view_count_str = created_at_view_count_str.split("(")[1].split(")")[0]
    view_count = int(view_count_str)

    title = soup.select("table > tbody > tr > td.req_first")[0].contents[0]

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


def crawl_view():
    """
    update all portal_view_count of portal articles
    from a week ago until now
    """
    now = timezone.datetime.today().date()
    log.info(f"crawl_view running on {now}")

    week_ago = (
        (datetime.today() - timedelta(days=7)).astimezone(KST).astimezone(timezone.utc)
    )

    session = _login_kaist_portal()

    def _get_board_week(page_num):
        board_req = session.get(
            f"{BASE_URL}/board/list.brd?boardId=today_notice&lang_knd=ko&userAgent=Chrome&isMobile=false&page={page_num}&userAgent=Chrome&isMobile=False&sortColumn=REG_DATIM&sortMethod=DESC",
            cookies=COOKIES,
        )
        soup = bs(board_req.text, "lxml")
        table = soup.select(".req_tbl_01")[0]
        info_list_per_page = []

        for row in table.find("tbody").find_all("tr"):
            cells = row.find_all("td")
            created_at_str = cells[4].text.strip()
            created_at = (
                datetime.strptime(created_at_str, "%Y.%m.%d")
                .astimezone(KST)
                .astimezone(timezone.utc)
            )

            if week_ago > created_at:
                return info_list_per_page, True  # stop

            info = {
                "title": cells[0].text.strip(),
                "view_count": int(cells[3].text.strip()),
                "link": cells[0].find("a").attrs["href"],
                "created_at": created_at,
            }

            info_list_per_page.append(info)

        return info_list_per_page, False

    info_list = []
    page_num = 1

    while True:
        info_list_per_page, stop = _get_board_week(page_num)
        info_list.extend(info_list_per_page)
        if stop:
            break

        page_num += 1

    if len(info_list) == 0:
        log.info("no portal notice in a week")
        return

    articles = Article.objects.filter(
        created_at__gte=week_ago, parent_board_id=PORTAL_NOTICE_BOARD_ID
    )
    article_dict = {}

    for a in articles:
        article_dict[a.url] = a

    new_portal_view_counts = []
    updated_articles = []

    for info in info_list:
        full_link = _list_link_to_full_link(info["link"])

        if full_link not in article_dict.keys():
            continue

        article = article_dict[full_link]

        portal_view_count = PortalViewCount(
            article=article,
            view_count=info["view_count"],
        )

        new_portal_view_counts.append(portal_view_count)

        article.latest_portal_view_count = info["view_count"]
        updated_articles.append(article)

    Article.objects.bulk_update(updated_articles, ["latest_portal_view_count"])
    PortalViewCount.objects.bulk_create(new_portal_view_counts)
    log.info(f"crawled view count of {len(new_portal_view_counts)} portal notices")


if __name__ == "__main__":
    _login_kaist_portal()
