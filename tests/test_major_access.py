from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.major.access import deny_major_comment_vote_access


class MajorCommentVoteAccessTest(SimpleTestCase):
    user = object()

    @staticmethod
    def comment(major_id):
        article = SimpleNamespace(related_major_id=major_id)
        return SimpleNamespace(parent_article=article, parent_comment=None)

    @patch("apps.major.access.can_read_major", return_value=True)
    def test_user_with_read_access_can_vote(self, can_read_major):
        comment = self.comment(major_id=123)

        self.assertFalse(deny_major_comment_vote_access(self.user, comment))
        can_read_major.assert_called_once_with(self.user, 123)

    @patch("apps.major.access.can_read_major", return_value=False)
    def test_user_without_read_access_cannot_vote(self, can_read_major):
        comment = self.comment(major_id=123)

        self.assertTrue(deny_major_comment_vote_access(self.user, comment))
        can_read_major.assert_called_once_with(self.user, 123)

    @patch("apps.major.access.can_read_major", return_value=True)
    def test_nested_comment_uses_parent_article(self, can_read_major):
        article = SimpleNamespace(related_major_id=456)
        parent_comment = SimpleNamespace(parent_article=article)
        comment = SimpleNamespace(
            parent_article=None,
            parent_comment=parent_comment,
        )

        self.assertFalse(deny_major_comment_vote_access(self.user, comment))
        can_read_major.assert_called_once_with(self.user, 456)

    @patch("apps.major.access.can_read_major")
    def test_general_comment_is_unchanged(self, can_read_major):
        comment = self.comment(major_id=None)

        self.assertFalse(deny_major_comment_vote_access(self.user, comment))
        can_read_major.assert_not_called()
