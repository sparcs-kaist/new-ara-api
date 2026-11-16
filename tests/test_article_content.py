import html.entities
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.models import Article, Board
from apps.core.serializers.article import BaseArticleSerializer
from ara.article_content import (
    FORMAT,
    normalize_stored_content,
    sanitize_article_content,
)
from ara.db.models import MetaDataModel
from ara.sanitizer import sanitize


def document(text, marks=None):
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return {"type": "doc", "content": [{"type": "paragraph", "content": [node]}]}


def text_of(content):
    return json.loads(content)["content"][0]["content"][0]["text"]


class ArticleContentTest(SimpleTestCase):
    def test_native_json_preserves_text_and_literal_entity_syntax(self):
        text = "<Perception> &lt;literal&gt; \"quotes\" 'apostrophe' & 😀"
        stored = sanitize_article_content(json.dumps(document(text)))
        self.assertEqual(text_of(stored), text)
        self.assertEqual(json.loads(stored)["ara_format"], FORMAT)

    def test_all_html5_entity_spellings_remain_literal_in_native_json(self):
        text = " ".join("&" + name for name in html.entities.html5)
        self.assertEqual(
            text_of(sanitize_article_content(json.dumps(document(text)))), text
        )

    def test_url_text_does_not_get_linkified_inside_json(self):
        text = 'https://example.com/?a=1&b=2 "quoted"'
        stored = sanitize_article_content(json.dumps(document(text)))
        self.assertEqual(text_of(stored), text)
        self.assertNotIn("<a ", stored)

    def test_save_read_edit_cycles_do_not_decode_again(self):
        text = "<Perception> &lt;literal&gt; &amp;lt; &#60; &#x3C; &amp"
        content = json.dumps(document(text))
        for _ in range(4):
            content = normalize_stored_content(sanitize_article_content(content))
            self.assertEqual(text_of(content), text)
            # TipTap strips the storage metadata when editing an existing post.
            edited = json.loads(content)
            edited.pop("ara_format")
            content = json.dumps(edited)

    def test_legacy_entities_are_decoded_once_after_parsing(self):
        legacy = json.dumps(
            document("&lt;Perception&gt; &quot;이름&quot; &#x1F600; &amp;lt;")
        )
        normalized = normalize_stored_content(legacy)
        self.assertEqual(text_of(normalized), '<Perception> "이름" 😀 &lt;')
        self.assertEqual(normalize_stored_content(normalized), normalized)
        self.assertEqual(sanitize_article_content(normalized), normalized)

    def test_legacy_linkification_corruption_is_repaired_at_storage_boundary(self):
        text = 'https://example.com/?a=1&b=2 "인용"'
        legacy = sanitize(json.dumps(document(text), ensure_ascii=False))
        with self.assertRaises(json.JSONDecodeError):
            json.loads(legacy)
        self.assertEqual(text_of(normalize_stored_content(legacy)), text)

    def test_link_and_image_attributes_are_preserved_without_html_escaping(self):
        url = "https://example.com/?a=1&b=2"
        doc = document(
            "링크", [{"type": "link", "attrs": {"href": url, "target": "_blank"}}]
        )
        doc["content"][0]["content"].append(
            {
                "type": "attachmentImage",
                "attrs": {
                    "src": "https://newara.cdn.sparcs.org/a.png",
                    "width": 500,
                    "alt": "<이미지>",
                },
            }
        )
        parsed = json.loads(sanitize_article_content(json.dumps(doc)))
        nodes = parsed["content"][0]["content"]
        self.assertEqual(nodes[0]["marks"][0]["attrs"]["href"], url)
        self.assertEqual(
            nodes[0]["marks"][0]["attrs"]["rel"], "noopener noreferrer nofollow"
        )
        self.assertEqual(nodes[1]["attrs"], doc["content"][0]["content"][1]["attrs"])

    def test_json_url_and_attribute_sanitization(self):
        for url in (
            "javascript:alert(1)",
            "java\nscript:alert(1)",
            "data:text/html,test",
            "jav&#97;script:alert(1)",
        ):
            with self.subTest(url=url):
                doc = document(
                    "text",
                    [{"type": "link", "attrs": {"href": url, "onclick": "alert(1)"}}],
                )
                mark = json.loads(sanitize_article_content(json.dumps(doc)))["content"][
                    0
                ]["content"][0]["marks"][0]
                self.assertNotIn("href", mark["attrs"])
                self.assertNotIn("onclick", mark["attrs"])
        for url in (
            "https://evilkaist.ac.kr/a.png",
            "//evil.example/a.png",
            "https://evil.example\\@sparcs.org/a.png",
            "data:image/svg+xml,test",
        ):
            with self.subTest(image=url):
                doc = {
                    "type": "doc",
                    "content": [
                        {
                            "type": "attachmentImage",
                            "attrs": {"src": url, "onerror": "alert(1)"},
                        }
                    ],
                }
                attrs = json.loads(sanitize_article_content(json.dumps(doc)))[
                    "content"
                ][0]["attrs"]
                self.assertNotIn("src", attrs)
                self.assertNotIn("onerror", attrs)

    def test_text_styles_and_code_blocks_are_plain_data(self):
        doc = document(
            "<Perception>", [{"type": "textStyle", "attrs": {"color": "#ed3a3a"}}]
        )
        doc["content"].append(
            {
                "type": "codeBlock",
                "attrs": {"language": "html"},
                "content": [{"type": "text", "text": '<a href="x">&lt;</a>'}],
            }
        )
        parsed = json.loads(sanitize_article_content(json.dumps(doc)))
        parsed.pop("ara_format")
        self.assertEqual(parsed, doc)

    def test_legacy_html_keeps_its_html_sanitization(self):
        content = (
            "<p>&lt;Perception&gt; <strong>서식</strong><script>alert(1)</script></p>"
        )
        self.assertEqual(sanitize_article_content(content), sanitize(content))
        self.assertEqual(normalize_stored_content(content), content)
        self.assertEqual(
            sanitize_article_content(content, sanitize_html=False), content
        )

    def test_model_save_preserves_native_json(self):
        text = "<Perception> &lt;literal&gt;"
        article = Article(
            parent_board=Board(is_readonly=False), content=json.dumps(document(text))
        )
        with patch.object(MetaDataModel, "save"):
            article.save()
        self.assertEqual(text_of(article.content), text)

    def test_loaded_legacy_article_is_normalized_before_an_unrelated_save(self):
        legacy = sanitize(json.dumps(document("<Perception> &")))
        article = Article.from_db("default", ["id", "content"], [1, legacy])
        article.parent_board = Board(is_readonly=False)
        article.parent_topic = None
        with patch.object(MetaDataModel, "save"):
            article.save()
        self.assertEqual(text_of(article.content), "<Perception> &")
        self.assertEqual(normalize_stored_content(article.content), article.content)

    def test_serialization_preserves_masking_and_normalizes_cached_legacy_objects(self):
        serializer = BaseArticleSerializer()
        article = SimpleNamespace(content=json.dumps(document("&lt;Perception&gt;")))
        with patch.object(serializer, "visible_verdict", return_value=True):
            self.assertEqual(text_of(serializer.get_content(article)), "<Perception>")
        with patch.object(serializer, "visible_verdict", return_value=False):
            self.assertIsNone(serializer.get_content(article))
