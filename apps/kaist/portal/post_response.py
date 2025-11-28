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
    inqCnt: int # 조회수
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
    board: BoardDetail

class BoardDetail(TypedDict):
    boardNo : int
    menuNo : int
    menuNm : str
    boardNm : str

class RecentPostItem(TypedDict):
    rnum : str # 순번. 가장 최근 것 부터 1, 2, ... 10
    pstNo : int
    boardNo : int
    delYn : BoolFlag
    ntcYn : BoolFlag
    otptYn : BoolFlag

class RecentPostListResponse(TypedDict):
    data : list[RecentPostItem]
