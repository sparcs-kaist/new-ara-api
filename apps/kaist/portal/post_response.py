from typing import Literal, TypedDict

BoolFlag = Literal["Y", "N"]


class PostResponse(TypedDict):
    pstNo: int
    boardNo: int
    pstGroupNo: int
    pstGroupLvl: int
    pstGroupCnt: int
    pstTtl: str
    pstCn: str
    delYn: BoolFlag
    ntcYn: BoolFlag
    otptYn: BoolFlag
    publicYn: BoolFlag
    atchFileCnt: int
    rcmdtnCnt: int
    cmntCnt: int
    inqCnt: int
    pstWrtrId: str
    pstWrtrNm: str
    pstWrtrDeptNm: str
    pstWrtrEml: str
    regDt: str
    regUser: str
    chgDt: str
    chgUser: str
    isAllDay: BoolFlag
    prevPstNo: int
    nextPstNo: int
    prevPstTtl: str
    nextPstTtl: str
