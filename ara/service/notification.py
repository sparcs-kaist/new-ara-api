from fastapi import HTTPException
from sqlalchemy.orm import Session
from ara.infra.notification import NotificationRepository
from ara.domain.notification import Notification
from ara.domain.user import User
from ara.domain.exceptions import EntityDoesNotExist
from ara.infra.firebase import fcm_notify_comment  # assuming fcm_notify_comment is imported from correct path
from ara.domain.article import Article  # Import Article and UserProfile from appropriate paths
from ara.domain.user_profile import UserProfile
from ara.domain.comment import Comment

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    def get_display_name(self, article: Article, profile: UserProfile) -> str:
        """
        Returns the display name for an article based on its name type and user profile.
        """
        if article.name_type == NameType.REALNAME:
            return profile.realname
        elif article.name_type == NameType.REGULAR:
            return profile.nickname
        else:
            return "익명"

    async def notify_commented(self, comment: Comment) -> None:
        """
        Notifies users when a comment is added.
        """
        article = comment.parent_article if comment.parent_article else comment.parent_comment.parent_article

        if comment.created_by != article.created_by:
            await self._notify_article_commented(article, comment)

        if comment.parent_comment and comment.created_by != comment.parent_comment.created_by:
            await self._notify_comment_commented(article, comment)

    async def _notify_article_commented(self, parent_article: Article, comment: Comment) -> None:
        """
        Notifies the user when a comment is added to their article.
        """
        name = self.get_display_name(parent_article, comment.created_by.profile)
        title = f"{name} 님이 새로운 댓글을 작성했습니다."

        # Save the notification
        notification = Notification(
            type="article_commented",
            title=title,
            content=comment.content[:32],  # Truncate content if necessary
            related_article=parent_article,
            related_comment=None
        )
        await self.notification_repo.save(notification)

        # Send push notification
        await fcm_notify_comment(parent_article.created_by, title, comment.content[:32], f"post/{parent_article.id}")

    async def _notify_comment_commented(self, parent_article: Article, comment: Comment) -> None:
        """
        Notifies the user when a comment is added to their comment.
        """
        name = self.get_display_name(parent_article, comment.created_by.profile)
        title = f"{name} 님이 새로운 대댓글을 작성했습니다."

        # Save the notification
        notification = Notification(
            type="comment_commented",
            title=title,
            content=comment.content[:32],  # Truncate content if necessary
            related_article=parent_article,
            related_comment=comment.parent_comment
        )
        await self.notification_repo.save(notification)

        # Send push notification
        await fcm_notify_comment(comment.parent_comment.created_by, title, comment.content[:32], f"post/{parent_article.id}")
