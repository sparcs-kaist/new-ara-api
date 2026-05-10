"""OTL backend HTTP client.

Ara 가 OTL 에 호출할 때 OneApp 공유 JWT secret 으로 토큰을 sign 한다.
호출 단위가 sync 한 번 (= 사용자가 /api/courses/me/ 호출 시) 이므로 별도
풀/리트라이/circuit breaker 는 두지 않는다. 실패하면 caller 가 stale 데이터로
fallback 한다.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import jwt
import requests
from django.conf import settings

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = (5, 30)  # (connect, read)
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 60  # sync 한 번 다 도는데 필요한 시간이면 충분


class OtlApiError(Exception):
    """OTL API 호출 실패."""


class OtlAuthError(OtlApiError):
    """OTL 가 401/403 응답 — JWT 무효 또는 OTL 쪽 user 없음."""


def _sign_jwt(uid: str) -> str:
    now = int(time.time())
    payload = {"uid": uid, "iat": now, "exp": now + JWT_TTL_SECONDS}
    return jwt.encode(payload, settings.ONE_APP_JWT_SECRET, algorithm=JWT_ALGORITHM)


def _request(method: str, path: str, uid: str, **kwargs: Any) -> Any:
    url = settings.OTL_API_BASE_URL.rstrip("/") + path
    headers = kwargs.pop("headers", {}) or {}
    headers["Authorization"] = f"Bearer {_sign_jwt(uid)}"

    try:
        resp = requests.request(
            method, url, headers=headers, timeout=REQUEST_TIMEOUT, **kwargs
        )
    except requests.RequestException as e:
        raise OtlApiError(f"OTL request to {path} failed: {e!r}") from e

    if resp.status_code in (401, 403):
        raise OtlAuthError(
            f"OTL auth rejected ({resp.status_code}) at {path}: {resp.text[:200]}"
        )
    if resp.status_code >= 400:
        raise OtlApiError(
            f"OTL {resp.status_code} at {path}: {resp.text[:200]}"
        )
    if not resp.content:
        return None
    try:
        return resp.json()
    except ValueError as e:
        raise OtlApiError(f"OTL response not JSON at {path}: {e!r}") from e


def get_user_info(uid: str) -> dict:
    """GET <base>/v2/users/info — {id, name, mail, studentNumber, ...}.

    base 는 환경별로 다름:
    - prod: https://otl.sparcs.org/api  (path-prefix /api)
    - dev:  https://api.otl.dev.sparcs.org  (subdomain)
    둘 다 path 는 /v2/... 로 통일.
    """
    return _request("GET", "/v2/users/info", uid)


def get_user_lectures(uid: str, otl_user_id: int) -> dict:
    """GET <base>/v2/users/<otl_user_id>/lectures — LecturesResponse."""
    return _request("GET", f"/v2/users/{otl_user_id}/lectures", uid)


def get_course_detail(uid: str, otl_course_id: int) -> dict:
    """GET <base>/v2/courses/<id> — Detail (credit, department, ...)."""
    return _request("GET", f"/v2/courses/{otl_course_id}", uid)
