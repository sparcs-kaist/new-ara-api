"""인스타그램 공개 게시물 수집 (비로그인).

로그인 없이 웹 프로필 엔드포인트를 쓰므로 서버 IP 가 429 나 로그인 요구로 막힐 수 있고,
응답 구조도 예고 없이 바뀐다. 실패는 모두 이 모듈 경계에서 잡아 로그만 남기고 빈 결과를 돌려준다.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

PROFILE_URL = "https://www.instagram.com/api/v1/users/web_profile_info/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    # 인스타 웹이 쓰는 공개 app id. 없으면 바로 400 이 온다
    "X-IG-App-ID": "936619743392459",
}
REQUEST_TIMEOUT = (5, 20)  # (connect, read)
FETCH_ERRORS = (requests.RequestException, ValueError, KeyError, TypeError)


@dataclass(frozen=True)
class InstagramPost:
    post_id: str
    taken_at: datetime
    image_urls: Tuple[str, ...]


def fetch_recent_posts(username: str) -> List[InstagramPost]:
    try:
        res = requests.get(PROFILE_URL, params={"username": username}, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        # 로그인 요구는 200 + HTML 로 오기도 한다 -> json() 에서 ValueError
        edges = res.json()["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
        return [post for post in (to_post(edge["node"]) for edge in edges) if post.image_urls]
    except FETCH_ERRORS as e:
        logger.warning("Instagram fetch failed for %s: %r", username, e)
        return []


def download_image(url: str) -> Optional[bytes]:
    try:
        res = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return res.content
    except requests.RequestException as e:
        logger.warning("Instagram image download failed: %r", e)
        return None


# 여러 장 게시물은 사진만 순서대로, 영상은 뺀다
def to_post(node: dict) -> InstagramPost:
    children = [edge["node"] for edge in (node.get("edge_sidecar_to_children") or {}).get("edges", [])]
    media = children or [node]
    return InstagramPost(
        post_id=str(node["id"]),
        taken_at=datetime.fromtimestamp(node["taken_at_timestamp"], tz=timezone.utc),
        image_urls=tuple(item["display_url"] for item in media if not item.get("is_video")),
    )
