from ara.domain.board.type import BoardInfo
from ara.infra.board.board_infra import BoardInfra


class BoardDomain:
    def __init__(self) -> None:
        self.board_infra = BoardInfra()

    def get_all_boards(self) -> list[BoardInfo]:
        return self.board_infra.get_all_boards()
