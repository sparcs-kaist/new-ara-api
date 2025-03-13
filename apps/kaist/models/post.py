from django.db import models

from apps.kaist.portal.post_response import PostResponse as PostDict


class Post(models.Model):
    id = models.BigIntegerField(primary_key=True)

    title = models.CharField(max_length=256, db_index=True)
    content = models.TextField()

    prev_post_id = models.BigIntegerField(null=True, blank=True)
    next_post_id = models.BigIntegerField(null=True, blank=True)

    board_id = models.IntegerField()
    group_id = models.IntegerField()
    group_level = models.IntegerField()
    group_count = models.IntegerField()

    is_deleted = models.BooleanField()
    is_public = models.BooleanField()

    attachment_count = models.SmallIntegerField()
    view_count = models.SmallIntegerField()

    writer_id = models.CharField(max_length=32)
    writer_name = models.CharField(max_length=32)
    writer_department = models.CharField(max_length=128, null=True, blank=True)
    writer_email = models.CharField(max_length=64, null=True, blank=True)

    registered_at = models.DateTimeField()
    registered_user_id = models.CharField(max_length=32)

    changed_at = models.DateTimeField()
    changed_user_id = models.CharField(max_length=32)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def from_typed_dict(post: PostDict):
        return Post(
            id=post["pstNo"],
            title=post["pstTtl"],
            content=post["pstCn"],
            prev_post_id=post["prevPstNo"],
            next_post_id=post["nextPstNo"],
            board_id=post["boardNo"],
            group_id=post["pstGroupNo"],
            group_level=post["pstGroupLvl"],
            group_count=post["pstGroupCnt"],
            is_deleted=post["delYn"] == "Y",
            is_public=post["publicYn"] == "Y",
            attachment_count=post["atchFileCnt"],
            view_count=post["inqCnt"],
            writer_id=post["pstWrtrId"],
            writer_name=post["pstWrtrNm"],
            writer_department=post["pstWrtrDeptNm"],
            writer_email=post["pstWrtrEml"],
            registered_at=post["regDt"],
            registered_user_id=post["regUser"],
            changed_at=post["chgDt"],
            changed_user_id=post["chgUser"],
        )

    def __str__(self):
        return f"{self.title} ({self.id})"
