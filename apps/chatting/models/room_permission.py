from enum import Enum
import datetime

from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel

# 각각의 채팅방에서 사용자의 역할
class ChatUserRole(str, Enum):
    OWNER = "OWNER"              # 소유자 - 채팅방 최고 관리자 처음에는 생성자.
    ADMIN = "ADMIN"              # 관리자 - 채팅방 관리 권한을 가진 사람
    PARTICIPANT = "PARTICIPANT"   # 참여자 - 채팅에 참여할 수 있는 사람
    OBSERVER = "OBSERVER"        # 관전자 - 채팅을 볼 수만 있는 사람
    BLOCKED = "BLOCKED"          # 차단됨 - 채팅방에서 차단된 사람
    BLOCKER = "BLOCKER"         # 채팅방을 차단한 사람 (초대 거부)

class ChatRoomPermission(MetaDataModel):
    # permission이 적용될 채팅방
    room_id : int = models.PositiveIntegerField(
        verbose_name = "채팅방 ID",
        default = None,
        blank = False,
        null = True,
        index = True,
        unique= True, #하나의 채팅방에는 하나의 권한 관리 체계만 존재
    ),
    # 입장 권한 (전체 or Invited)
    entrance_permission : str = models.CharField(
        verbose_name = "입장 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("INVITED", "초대받은 사용자만"),
        ],
        default = "INVITED",
        blank = False,
        null = False,
    ),
    # 초대할 수 있는 사용자
    invite_permission : str = models.CharField(
        verbose_name = "초대 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자만"),
            ("OWNER", "소유자만"),
        ],
        default = "ALL",
        blank = False,
        null = False,
    ),
    # 메세지 보내기 권한
    messagee_permisson : str = models.CharField(
        verbose_name = "메세지 보내기 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자만"),
            ("OWNER", "소유자만"),
            ("PARTICIPANT", "참여자만"),
        ],
        default = "ALL",
        blank = False,
        null = False,
    ),
    # 유저 강퇴 권한
    kick_permission : str = models.CharField(
        verbose_name = "유저 강퇴 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자만"),
            ("OWNER", "소유자만"),
            ("PARTICIPANT", "참여자만"),
        ],
        default = "ALL",
        blank = False,
        null = False,
    ),
    permission_update_permmission : str = models.CharField(
        verbose_name = "권한 업데이트 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자만"),
            ("OWNER", "소유자만"),
        ],
        default = "OWNER",
        blank = False,
        null = False,
    ),

    # created_at : 채팅방이 처음 생성될 때 같이 생성됨
    # deleted_at : 채팅방이 삭제될 때 같이 삭제됨
