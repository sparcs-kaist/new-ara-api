from datetime import datetime

from pydantic import BaseModel

from ara.domain.board.constants import NameType


class BoardGroupInfo(BaseModel):
    id: int
    ko_name: str
    en_name: str
    slug: str


class TopicInfo(BaseModel):
    slug: str
    ko_name: str
    en_name: str


class BoardInfo(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime
    slug: str
    ko_name: str
    en_name: str
    # TODO(hyuk): 이거 group_has_access_permission 여기 잘보고 뭐 할거 판단
    read_access_mask: int
    write_access_mask: int
    comment_access_mask: int
    is_readonly: bool
    is_hidden: bool
    name_type: NameType
    is_school_communication: int
    group: BoardGroupInfo
    banner_image: str
    ko_banner_description: str
    en_banner_description: str
    top_threshold: int
    topics: list[TopicInfo]

    class Config:
        arbitrary_types_allowed = True
