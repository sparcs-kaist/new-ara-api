from enum import Enum
import datetime

from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel


class ChatRoomType(str, Enum):
    DM = "DM" # 1:1 채팅방
    GROUP_DM = "GROUP_DM" # 그룹 채팅방 (permission이 없이 유저 모두 동일한 참여자.)
    OPEN_CHAT = "OPEN_CHAT" # 오픈 그룹 채팅방 (role에 따라 permission이 설정된다.)

class ChatNameType(str, Enum):
    NICKNAME = "NICKNAME"  # 닉네임
    ANONYMOUS = "ANONYMOUS"  # 익명
    REAL_NAME = "REAL_NAME"  # 실명

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoom(MetaDataModel):
    room_title : str = models.CharField(
        verbose_name = "채팅방 이름",
        max_length = 100,
        default = "아라 채팅방",
        blank = False,
        null = False,
    )
    room_id : int = models.PositiveIntegerField(
        verbose_name = "room_id",
        default = 0,
        db_index = True,
        unique = True,
    )
    # 채팅방 타입
    room_type : ChatRoomType = models.CharField(
        verbose_name = "room_type",
        max_length = 20,
        choices = [(room_type.value, room_type.name) for room_type in ChatRoomType],
        default = ChatRoomType.OPEN_CHAT.value,
        blank = False,
        null = False,
    )
    # 채팅방에서 이름 표시 방식
    chat_name_type : str = models.CharField(
        verbose_name= "chat_name_type",
        max_length = 20,
        choices= [(name_type.value, name_type.name) for name_type in ChatNameType],
        default = ChatNameType.NICKNAME.value,
        blank = False,
        null = False,
    )
    #채팅방의 권한 부여 방식 - 다른 DB 테이블로 빠짐
    # self.room_permission

    #최근 메시지가 온 시간
    recent_message_at = models.DateTimeField(
        verbose_name= "recent_message_at",
        null = True,
        blank = False,
        auto_now = False,
        default = None,
    )
    # 가장 최근의 메시지
    recent_message = models.OneToOneField(
        "chatting.ChatMessage", #순환 참조 막기 위해 문자열 참조로 우회
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recent_for_room'
    )

    #created_at : 채팅방 생성 시
    #deleted_at : 채팅방이 삭제되었을 때

    @classmethod
    @transaction.atomic
    def create(cls, **kwargs):
        # race_condition 방지: 채팅방 row에 락을 걸고 가장 큰 room_id를 가져옴
        last_room = cls.objects.select_for_update().order_by('-room_id').first()
        kwargs['room_id'] = (last_room.room_id if last_room else 0) + 1
        return super().create(**kwargs)

    #User가 room에 참여 했는지 return
    def is_user_participated(self, user) -> bool:
        return self.membership_info_set.filter(user=user).exists()

    #User가 room에 참여 가능한지 판단
    def can_user_participate(self, user) -> bool:
        # 이미 참여한 경우 초대 정보가 없어지므로 Serialize 에서 이 함수를 호출하지 말아야 한다.
        # OPEN_CHAT의 경우, 권한 테이블의 entrance_permission이 ALL이면 누구나 참여 가능
        if self.room_type == ChatRoomType.OPEN_CHAT:
            return self.room_permission.entrance_permission == "ALL"
        
        elif self.room_type == ChatRoomType.GROUP_DM or self.room_type == ChatRoomType.DM:
            return True

        # 그 외의 경우 초대장이 있는지 확인
        else:
            return self.invitation_set.filter(invitation_to=user, deleted_at=None).exists()

    #User가 room에 어떤 permission을 가지고 있는지 return
    def get_permission_info(self, user):
        return self.membership_info_set.filter(user=user, chat_room=self).first()

    #Room에 있는 메시지 가져오기
    def get_messages(self, start_index=0, end_index=100):
        """
        start_index : 가져올 메시지의 시작 인덱스 (0부터 시작, 가장 최근 메시지가 0번째)
        end_index : 가져올 메시지의 끝 인덱스 (미포함)
        
        메시지 개수가 start_index 이상이면 빈 쿼리 반환
        """
        if start_index < 0 or end_index < 0 or start_index >= end_index:
            raise ValueError("start_index와 end_index를 올바르게 지정하세요.")

        total_count = self.message_set.count()

        if start_index >= total_count:
            return self.message_set.none()  # 빈 쿼리 반환

        if end_index > total_count:
            end_index = total_count  # 최대 개수까지만 허용

        messages = self.message_set.order_by("-id")[start_index:end_index]
        
        return messages