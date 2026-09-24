import logging
import os

import firebase_admin
from firebase_admin import credentials

from ara.settings.django import BASE_DIR

log = logging.getLogger(__name__)

# 토글: env 가 켜져 있고 cred 파일이 있을 때만 실제 발송. 둘 중 하나라도 빠지면 no-op.
FCM_ENABLED = False

_disabled = os.environ.get("FCM_DISABLED", "").strip().lower() in ("1", "true", "yes")
_cred_path = os.path.join(BASE_DIR, "firebaseServiceAccountKey.json")

if _disabled:
    log.info("FCM 꺼짐: FCM_DISABLED 환경변수")
elif not os.path.isfile(_cred_path):
    log.warning("FCM 꺼짐: 인증 파일이 없음 (%s)", _cred_path)
else:
    try:
        firebase_admin.initialize_app(credentials.Certificate(_cred_path))
        FCM_ENABLED = True
    except Exception as e:
        log.error("FCM 꺼짐: firebase 초기화 실패 (%r)", e)
