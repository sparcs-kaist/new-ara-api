import json
from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.core.models import Article, Board
from ara.sanitizer import sanitize
from tests.conftest import TestCase


def editor_content(text: str) -> str:
    return json.dumps(
        {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            ],
        }
    )


@override_settings(ELASTICSEARCH_DSL_AUTOSYNC=False)
@pytest.mark.usefixtures("set_user_client")
class TestArticleContentTextSave(TestCase):
    def setUp(self):
        self.board = Board.objects.create(ko_name="본문 추출", en_name="Content extraction")
        self.article = Article.objects.create(
            title="제목",
            content=editor_content("원래 본문"),
            created_by=self.user,
            parent_board=self.board,
        )

    def test_create_and_content_edit_extract_once_each(self):
        article = Article(
            title="새 글",
            content=editor_content("새 본문"),
            created_by=self.user,
            parent_board=self.board,
        )
        with patch.object(
            article, "extract_text_from_json", wraps=article.extract_text_from_json
        ) as extract:
            article.save()
            assert article.content_text == "새 본문"
            article.save()
            assert extract.call_count == 1
            article.content = editor_content("수정 본문")
            article.save()
            article.save()
            assert extract.call_count == 2
        article.refresh_from_db()
        assert article.content_text == "수정 본문"

    def test_counter_and_title_updates_do_not_reprocess_content(self):
        article = self.article
        with patch.object(
            article, "extract_text_from_json", wraps=article.extract_text_from_json
        ) as extract, patch(
            "apps.core.models.article.sanitize", wraps=sanitize
        ) as sanitize_content:
            article.update_hit_count()
            article.update_vote_status()
            article.update_comment_count()
            article.update_report_count()
            article.title = "제목만 수정"
            article.save()
            extract.assert_not_called()
            sanitize_content.assert_not_called()
        article.refresh_from_db()
        assert article.content_text == "원래 본문"

    def test_loaded_article_with_unchanged_body_does_not_extract(self):
        article = Article.objects.get(pk=self.article.pk)
        with patch.object(
            article, "extract_text_from_json", wraps=article.extract_text_from_json
        ) as extract:
            article.save()
            extract.assert_not_called()

    def test_partial_body_save_persists_search_text(self):
        article = self.article
        for fields, text in [(["content"], "수정 본문"), (iter(["content"]), "다시 수정")]:
            article.content = editor_content(text)
            article.save(update_fields=fields)
            article.refresh_from_db()
            assert article.content_text == text

    def test_counter_only_save_leaves_pending_body_edit_for_later(self):
        article = self.article
        article.content = editor_content("아직 저장하지 않은 본문")
        with patch.object(
            article, "extract_text_from_json", wraps=article.extract_text_from_json
        ) as extract:
            article.hit_count = 1
            article.save(update_fields=["hit_count"])
            extract.assert_not_called()
            stored = Article.objects.get(pk=article.pk)
            assert stored.content_text == "원래 본문"
            assert stored.content == editor_content("원래 본문")
            article.save(update_fields=["content"])
            extract.assert_called_once()
        article.refresh_from_db()
        assert article.content_text == "아직 저장하지 않은 본문"

    def deferred_article(self):
        return (
            Article.objects.only(
                "id", "hit_count", "parent_board", "parent_topic", "deleted_at"
            )
            .select_related("parent_board")
            .get(pk=self.article.pk)
        )

    def test_deferred_body_is_not_loaded_on_counter_save(self):
        for partial in (False, True):
            article = self.deferred_article()
            with self.assertNumQueries(1):
                article.hit_count += 1
                article.save(**({"update_fields": ["hit_count"]} if partial else {}))
            assert "content" not in article.__dict__
            assert "content_text" not in article.__dict__

    def test_editing_deferred_body_persists_search_text(self):
        article = self.deferred_article()
        article.content = editor_content("미리 읽지 않은 본문 수정")
        article.save()
        stored = Article.objects.get(pk=article.pk)
        assert stored.content_text == "미리 읽지 않은 본문 수정"

    def test_refresh_updates_body_snapshot(self):
        article = self.article
        Article.objects.filter(pk=article.pk).update(
            content=editor_content("다른 경로에서 수정"), content_text="다른 경로에서 수정"
        )
        article.refresh_from_db()
        with patch.object(
            article, "extract_text_from_json", wraps=article.extract_text_from_json
        ) as extract:
            article.hit_count += 1
            article.save()
            extract.assert_not_called()
        assert article.content_text == "다른 경로에서 수정"

    def test_partial_refresh_preserves_pending_body_edit(self):
        article = self.article
        article.content = editor_content("수정 본문")
        article.refresh_from_db(fields=["hit_count"])
        article.save()
        article.refresh_from_db()
        assert article.content_text == "수정 본문"

    def test_html_and_empty_body_edits_refresh_search_text(self):
        article = self.article
        for content, expected in [("<p>HTML 본문</p>", "HTML 본문"), ("", "")]:
            article.content = content
            article.save(update_fields=["content"])
            article.refresh_from_db()
            assert article.content_text == expected
