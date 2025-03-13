from datetime import datetime

import requests
from django.utils import timezone as django_timezone
from pytz import timezone as pytz_timezone

from apps.kaist.models import Post
from apps.kaist.portal.post_response import PostResponse
from ara.settings import PORTAL_JSESSIONID


class SessionExpiredException(Exception):
    ...


class Crawler:
    _session = requests.Session()
    _session_id = PORTAL_JSESSIONID

    _KST = pytz_timezone("Asia/Seoul")

    @classmethod
    def _parse_datetime_string(cls, datetime_str: str) -> datetime:
        return (
            datetime.strptime(datetime_str, "%Y.%m.%d %H:%M:%S")
            .astimezone(cls._KST)
            .astimezone(django_timezone.utc)
        )

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
            prev_post_id=res["nextPstNo"],
            next_post_id=res["prevPstNo"],
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

        response = cls._session.get(
            url=f"https://portal.kaist.ac.kr/wz/api/board/recents/{post_id}?menuNo=21",
            cookies={"JSESSIONID": cls._session_id},
        )

        if "application/json" not in response.headers["Content-Type"]:
            # TODO: Send an alert to the admin
            raise SessionExpiredException(f"Failed to get post {post_id}")

        post = cls._parse_response(response.json())
        return post

    @classmethod
    def find_next_post(cls, post: Post) -> Post | None:
        if post.next_post_id is None:
            return None
        return cls.get_post(post.next_post_id)

    @classmethod
    def update_session_id(cls, session_id: str) -> None:
        cls.session_id = session_id
