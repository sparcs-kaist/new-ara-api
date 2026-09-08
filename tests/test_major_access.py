from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.permissions.comment import CommentPermission
from apps.major.access import deny_unreadable_major_comment_access


class MajorCommentVoteAccessTest(SimpleTestCase):
    user = object()

    @staticmethod
    def comment(major_id):
        article = SimpleNamespace(related_major_id=major_id)
        return SimpleNamespace(parent_article=article, parent_comment=None)

    @patch("apps.major.access.can_read_major", return_value=True)
    def test_user_with_read_access_can_vote(self, can_read_major):
        comment = self.comment(major_id=123)

        self.assertFalse(deny_unreadable_major_comment_access(self.user, comment))
        can_read_major.assert_called_once_with(self.user, 123)

    @patch("apps.major.access.can_read_major", return_value=False)
    def test_user_without_read_access_cannot_vote(self, can_read_major):
        comment = self.comment(major_id=123)

        self.assertTrue(deny_unreadable_major_comment_access(self.user, comment))
        can_read_major.assert_called_once_with(self.user, 123)

    @patch("apps.major.access.can_read_major", return_value=True)
    def test_nested_comment_uses_parent_article(self, can_read_major):
        article = SimpleNamespace(related_major_id=456)
        parent_comment = SimpleNamespace(parent_article=article)
        comment = SimpleNamespace(
            parent_article=None,
            parent_comment=parent_comment,
        )

        self.assertFalse(deny_unreadable_major_comment_access(self.user, comment))
        can_read_major.assert_called_once_with(self.user, 456)

    @patch("apps.major.access.can_read_major")
    def test_general_comment_is_unchanged(self, can_read_major):
        comment = self.comment(major_id=None)

        self.assertFalse(deny_unreadable_major_comment_access(self.user, comment))
        can_read_major.assert_not_called()


class MajorCommentObjectPermissionTest(SimpleTestCase):
    permission = CommentPermission()
    user = SimpleNamespace(id=1, is_staff=False)
    comment = SimpleNamespace(created_by=SimpleNamespace(id=2))

    @patch(
        "apps.major.access.deny_unreadable_major_comment_access",
        return_value=False,
    )
    @patch("apps.course.access.deny_unenrolled_comment_access", return_value=False)
    def test_favorite_major_can_retrieve_comment(self, deny_course, deny_unreadable):
        request = SimpleNamespace(user=self.user, method="GET")

        self.assertTrue(
            self.permission.has_object_permission(request, object(), self.comment)
        )
        deny_course.assert_called_once_with(self.user, self.comment)
        deny_unreadable.assert_called_once_with(self.user, self.comment)

    @patch("apps.major.access.deny_non_same_major_comment_access", return_value=True)
    @patch("apps.course.access.deny_unenrolled_comment_access", return_value=False)
    def test_favorite_major_cannot_modify_comment(self, deny_course, deny_not_same):
        request = SimpleNamespace(user=self.user, method="PATCH")

        self.assertFalse(
            self.permission.has_object_permission(request, object(), self.comment)
        )
        deny_course.assert_called_once_with(self.user, self.comment)
        deny_not_same.assert_called_once_with(self.user, self.comment)
