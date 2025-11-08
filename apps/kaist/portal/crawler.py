from datetime import datetime

import requests
from django.utils import timezone as django_timezone
from pytz import timezone as pytz_timezone

from apps.kaist.models import Post
from apps.kaist.portal.post_response import PostResponse, RecentPostListResponse, RecentPostItem
from ara import redis
from ara.log import log
from ara.settings import PORTAL_JSESSIONID


class SessionExpiredException(Exception):
    ...

class DeletedPostException(Exception):
    """
    recent post가 삭제된 경우 삭제된 경우 발생하는 exception : 크롤링 시작 지점 조정 필요
    """
    ...

class Crawler:
    SESSION_KEY = "JSESSIONID"
    SESSION_REDIS_KEY = "crawler:jsessionid"

    _session = requests.Session()
    _session.cookies.set(SESSION_KEY, PORTAL_JSESSIONID)

    _KST = pytz_timezone("Asia/Seoul")

    @classmethod
    def _parse_datetime_string(cls, datetime_str: str) -> datetime:
        return (
            datetime.strptime(datetime_str, "%Y.%m.%d %H:%M:%S")
            .astimezone(cls._KST)
            .astimezone(django_timezone.utc)
        )
    
    @classmethod
    def _is_deleted_post(cls, html_txt: str) -> bool:
        if not html_txt:
            return False
        # 삭제 판단의 기준이 되는 text
        mask_txt = ["서비스 이용에 불편을 드려 죄송합니다.", ]
        return any(txt in html_txt for txt in mask_txt)
    
    #post 사이의 링크가 끊긴 경우를 위해 현재를 기준으로 가장 최근 post id를 가져옵니다.
    @classmethod
    def _get_recent_post_id(cls) -> int:
        try:
            payload = resp.json()
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Failed to parse JSON. status={resp.status_code} url={resp.url} snippet={repr(resp.text)}"
            ) from e
        payload = resp.json()  # 제공된 응답은 유효 JSON
        items = payload["data"]
        items_sorted = sorted(items, key=lambda x: int(x["rnum"]))

        for post_item in items_sorted:
            if post_item["delYn"] == "N":
                return int(post_item["pstNo"])

    @classmethod
    def _parse_response(cls, res: PostResponse) -> Post:
        """
        Parse the response from the API and return a `Post` object.

        :param res: The response from the API
        """

        return Post(
            id=res["pstNo"],
            title=res["pstTtl"],
            content=res["pstCn"],
            # Swap values as the API response is incorrect (nextPstNo is actually prevPstNo)
            prev_post_id=res.setdefault("nextPstNo"),
            next_post_id=res.setdefault("prevPstNo"),
            board_id=res["boardNo"],
            group_id=res["pstGroupNo"],
            group_level=res["pstGroupLvl"],
            group_count=res["pstGroupCnt"],
            is_deleted=res["delYn"] == "Y",
            is_public=res["publicYn"] == "Y",
            attachment_count=res["atchFileCnt"],
            view_count=res["inqCnt"],
            writer_id=res["pstWrtrId"],
            writer_name=res["pstWrtrNm"],
            writer_department=res.setdefault("pstWrtrDeptNm"),
            writer_email=res.setdefault("pstWrtrEml"),
            registered_at=cls._parse_datetime_string(res["regDt"]),
            registered_user_id=res["regUser"],
            changed_at=cls._parse_datetime_string(res["chgDt"]),
            changed_user_id=res["chgUser"],
        )

    @classmethod
    def get_post(cls, post_id: int) -> Post:
        """
        Get a post from the portal.

        :param post_id: The ID of the post to get
        """

        retry_count = 1

        while retry_count >= 0:
            response = cls._session.get(
                f"https://portal.kaist.ac.kr/wz/api/board/recents/{post_id}"
            )

            if cls._has_fetched_successfully(response):
                post = cls._parse_response(response.json())
                return post
            
            if cls._is_deleted_post(response.text):
                raise DeletedPostException(f"Post {post_id} has been deleted")

            if retry_count == 0:
                raise SessionExpiredException(f"Failed to get post {post_id}")

            cls.update_session_id()
            retry_count -= 1

    @classmethod
    def _has_fetched_successfully(cls, response: requests.Response) -> bool:
        return "application/json" in response.headers["Content-Type"]

    @classmethod
    def find_next_post(cls, post: Post) -> Post | None:
        if post.next_post_id is None:
            return None
        try:
            return cls.get_post(post.next_post_id)
        except DeletedPostException:
            try:
                fresh = cls.get_post(post.id)
            except DeletedPostException:
                return None
            if fresh.next_post_id and fresh.next_post_id != post.next_post_id:
                return cls.get_post(fresh.next_post_id)
            return None

    @classmethod
    def update_session_id(cls) -> None:
        new_session_id = redis.get(cls.SESSION_REDIS_KEY).decode()
        if new_session_id is not None:
            log.info(
                f"KAIST Portal Crawler :: JSESSIONID updated to ({new_session_id})"
            )
            cls._session.cookies.set(cls.SESSION_KEY, new_session_id)
