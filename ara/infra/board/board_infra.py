from apps.core.models.board import Board
from apps.core.models.board_group import BoardGroup
from ara.domain.board.type import BoardGroupInfo, BoardInfo, TopicInfo
from ara.infra.django_infra import NewAraDjangoInfra


class BoardGroupInfra(NewAraDjangoInfra[BoardGroup]):
    def __init__(self) -> None:
        super().__init__(Board)

    pass


class BoardInfra(NewAraDjangoInfra[Board]):
    def __init__(self) -> None:
        super().__init__(Board)
        self.board_group_infra = BoardGroupInfra()

    def get_all_boards(self) -> list[BoardInfo]:
        queryset = Board.objects.select_related("group").extra(
            select={
                "topic_id": "topic.id",
                "topic_slug": "topic.slug",
                "topic_ko_name": "topic.ko_name",
                "topic_en_name": "topic.en_name",
            },
            tables=[
                "core_board` AS `b` LEFT OUTER JOIN `core_topic` AS `topic`"
                " ON `b`.`id` = `topic`.`parent_board_id"
            ],
            where=["b.id = core_board.id"],
        )

        d: dict[BoardInfo, BoardInfo] = {}
        for board_model in queryset:
            board_info = self._to_board_without_topics(board_model)
            if board_info.id in d.keys():
                d[board_info.id].topics.append(
                    TopicInfo(
                        slug=board_model.topic_slug,
                        ko_name=board_model.topic_ko_name,
                        en_name=board_model.topic_en_name,
                    )
                )
            else:
                if board_model.topic_id is None:
                    d[board_info.id] = board_info
                else:
                    board_info_with_topic = board_info
                    board_info_with_topic.topics.append(
                        TopicInfo(
                            slug=board_model.topic_slug,
                            ko_name=board_model.topic_ko_name,
                            en_name=board_model.topic_en_name,
                        )
                    )
                    d[board_info.id] = board_info_with_topic

        return [info for info in d.values()]

    def _to_board_without_topics(self, board: Board) -> BoardInfo:
        return BoardInfo(
            id=board.id,
            created_at=board.created_at,
            updated_at=board.updated_at,
            deleted_at=board.deleted_at,
            slug=board.slug,
            ko_name=board.ko_name,
            en_name=board.en_name,
            read_access_mask=board.read_access_mask,
            write_access_mask=board.write_access_mask,
            comment_access_mask=board.comment_access_mask,
            is_readonly=board.is_readonly,
            is_hidden=board.is_hidden,
            name_type=board.name_type,
            is_school_communication=board.is_school_communication,
            group=BoardGroupInfo(
                id=board.group.id,
                ko_name=board.group.ko_name,
                en_name=board.group.en_name,
                slug=board.group.slug,
            ),
            banner_image=board.banner_image.url,
            ko_banner_description=board.ko_banner_description,
            en_banner_description=board.en_banner_description,
            top_threshold=board.top_threshold,
            topics=[],
        )
