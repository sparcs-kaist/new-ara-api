from ara.domain.board.board_domain import BoardDomain
from ara.domain.board.type import BoardInfo


class BadgeApplication:
    def __init__(self) -> None:
        self.board_domain = BoardDomain()

    def get_all_boards(self) -> list[BoardInfo]:
        return self.board_domain.get_all_boards()
