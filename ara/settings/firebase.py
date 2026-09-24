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
    log.info("FCM disabled via FCM_DISABLED env var")
elif not os.path.isfile(_cred_path):
    log.warning("FCM disabled: cred file not found at %s", _cred_path)
else:
    try:
        firebase_admin.initialize_app(credentials.Certificate(_cred_path))
        FCM_ENABLED = True
    except Exception as e:
        log.error("FCM disabled: firebase init failed (%r)", e)
