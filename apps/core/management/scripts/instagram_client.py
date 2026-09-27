import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

PROFILE_URL = "https://www.instagram.com/{username}/"
# Sec-Fetch 헤더가 없으면 게시물 없는 빈 페이지가 온다
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
REQUEST_TIMEOUT = (5, 20)  # (connect, read)
FETCH_ERRORS = (requests.RequestException, ValueError, KeyError, TypeError)

TIMELINE_KEY = "polaris_ordered_timeline_connection"
JSON_SCRIPT_RX = re.compile(r'<script type="application/json"[^>]*>(.*?)</script>', re.S)
VIDEO = 2  # media_type. 1 사진, 8 여러 장
# 인스타 id 는 상위 비트가 2011-08-24 기준 ms 타임스탬프다
INSTAGRAM_EPOCH_MS = 1314220021721


@dataclass(frozen=True)
class InstagramPost:
    post_id: str
    taken_at: datetime
    image_urls: Tuple[str, ...]


def fetch_recent_posts(username: str) -> List[InstagramPost]:
    try:
        res = requests.get(PROFILE_URL.format(username=username), headers=HEADERS, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        nodes = [edge["node"] for edge in find_timeline(res.text)["edges"]]
        return [to_post(node) for node in nodes if node.get("media_type") != VIDEO]
    except FETCH_ERRORS as e:
        logger.warning("Instagram fetch failed for %s: %r", username, e)
        return []


def download_image(url: str) -> Optional[bytes]:
    try:
        res = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return res.content
    except requests.RequestException as e:
        logger.warning("Instagram image download failed: %r", e)
        return None


# 로그인 요구 페이지나 구조가 바뀐 페이지에는 타임라인이 없다 -> KeyError
def find_timeline(html: str) -> dict:
    for blob in JSON_SCRIPT_RX.findall(html):
        if TIMELINE_KEY in blob:
            timeline = search_key(json.loads(blob), TIMELINE_KEY)
            if timeline is not None:
                return timeline
    raise KeyError(TIMELINE_KEY)


def search_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        children = obj.values()
    elif isinstance(obj, list):
        children = obj
    else:
        return None
    for child in children:
        found = search_key(child, key)
        if found is not None:
            return found
    return None


def to_post(node: dict) -> InstagramPost:
    pk = int(node["pk"])
    return InstagramPost(
        post_id=str(pk),
        taken_at=datetime.fromtimestamp(((pk >> 23) + INSTAGRAM_EPOCH_MS) / 1000, tz=timezone.utc),
        image_urls=(node["display_uri"],),
    )
