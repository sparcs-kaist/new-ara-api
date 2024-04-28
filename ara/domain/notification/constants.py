from enum import IntFlag, auto

class NameType(IntFlag):
    REGULAR = auto()
    ANONYMOUS = auto()
    REALNAME = auto()