from django.db import models

# Log for crawled KAIST portal posts
class Post(models.Model):
    id = models.BigIntegerField(primary_key=True)

    title = models.CharField(max_length=256, db_index=True)
    content = models.TextField()

    prev_post_id = models.BigIntegerField(null=True, blank=True)
    next_post_id = models.BigIntegerField(null=True, blank=True)

    board_id = models.IntegerField()
    board_name = models.CharField(max_length=128, null=True, default=None)
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

    registered_at = models.DateTimeField(db_index=True)
    registered_user_id = models.CharField(max_length=32)

    changed_at = models.DateTimeField()
    changed_user_id = models.CharField(max_length=32)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.id})"
    
    #@Todo : parsing 해올때 foreign key로 article id 저장해놓기
    def get_ara_article(self) -> int | None:
        from apps.core.models import Article
        try:
            article = Article.objects.get(title=self.title)
            return article.id
        except Article.DoesNotExist:
            return None