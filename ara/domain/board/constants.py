from enum import IntEnum, IntFlag, auto


class BoardAccessPermissionType(IntEnum):
    READ = 0
    WRITE = 1
    COMMENT = 2


class NameType(IntFlag):
    REGULAR = auto()
    ANONYMOUS = auto()
    REALNAME = auto()
