from django.db import models
from apps.kaist.models import Post

class PostViewCountLog(models.Model):
    """
    게시물의 시간대별 조회수를 기록하는 모델
    """
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='view_count_logs',
        db_index=True
    )
    view_count = models.IntegerField(help_text="기록 시점의 조회수")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"Log(post={self.post_id}, views={self.view_count}, time={self.created_at})"