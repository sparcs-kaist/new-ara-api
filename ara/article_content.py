"""Keep TipTap JSON as structured data; HTML sanitization is for HTML only."""

import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from ara.sanitizer import sanitize

FORMAT = "ara-tiptap-v1"

NODE_ATTRIBUTES = {
    "doc": (),
    "paragraph": (),
    "text": (),
    "heading": ("level",),
    "blockquote": (),
    "bulletList": (),
    "orderedList": ("start",),
    "listItem": (),
    "codeBlock": ("language",),
    "hardBreak": (),
    "horizontalRule": (),
    "attachmentImage": ("src", "alt", "title", "width", "data-attachment"),
    "image": ("src", "alt", "title", "width", "height"),
    "linkBookmark": ("href", "title"),
}
MARK_ATTRIBUTES = {
    "bold": (),
    "italic": (),
    "strike": (),
    "underline": (),
    "code": (),
    "textStyle": ("color",),
    "link": ("href", "target", "rel"),
}
IMAGE_HOSTS = (
    "sparcs.org",
    "kaist.ac.kr",
    "sparcs-newara.s3.amazonaws.com",
    "sparcs-newara-dev.s3.amazonaws.com",
)


def _parse_document(content: str) -> dict | None:
    try:
        value = json.loads(content)
    except (ValueError, TypeError, RecursionError):
        return None
    if isinstance(value, dict) and value.get("type") == "doc":
        if isinstance(value.get("content", []), list):
            return value
    return None


def _safe_url(value: str, *, image: bool = False) -> bool:
    # Match the browser's handling of whitespace/control characters in schemes.
    normalized = re.sub(r"[\s\x00-\x20\x7f-\x9f]", "", html.unescape(value)).replace(
        "\\", "/"
    )
    try:
        parsed = urlsplit(normalized)
        if parsed.scheme.lower() not in ("", "http", "https", "mailto", "tel", "sms"):
            return False
        if image:
            if parsed.scheme.lower() not in ("", "http", "https"):
                return False
            hostname = parsed.hostname
            return not parsed.netloc or bool(
                hostname
                and any(
                    hostname == host or hostname.endswith("." + host)
                    for host in IMAGE_HOSTS
                )
            )
        return True
    except ValueError:
        return False


def _clean_attributes(attrs: object, allowed: tuple) -> dict:
    if not isinstance(attrs, dict):
        return {}
    result = {}
    for key in allowed:
        value = attrs.get(key)
        if value is None:
            continue
        if key in ("level", "start", "width", "height"):
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                result[key] = min(value, 3) if key == "level" else value
        elif isinstance(value, str):
            if key in ("href", "src") and not _safe_url(value, image=key == "src"):
                continue
            if key == "target" and value not in ("_blank", "_self"):
                continue
            if key == "color" and not re.fullmatch(
                r"#[\da-fA-F]{3,8}|[a-zA-Z]+|(?:rgb|hsl)a?\([\d.,%\s+\-]+\)", value
            ):
                continue
            result[key] = value
    if result.get("target") == "_blank":
        result["rel"] = "noopener noreferrer nofollow"
    return result


def _clean_node(node: object, *, mark: bool = False, depth: int = 0) -> dict | None:
    if not isinstance(node, dict) or depth > 100:
        return None
    attributes = MARK_ATTRIBUTES if mark else NODE_ATTRIBUTES
    kind = node.get("type")
    if not isinstance(kind, str) or kind not in attributes:
        return None
    result = {"type": kind}
    if kind == "text":
        if not isinstance(node.get("text"), str) or not node["text"]:
            return None
        result["text"] = node["text"]
    if "attrs" in node:
        result["attrs"] = _clean_attributes(node["attrs"], attributes[kind])
    if not mark:
        for key in ("content", "marks"):
            if isinstance(node.get(key), list):
                result[key] = [
                    cleaned
                    for child in node[key]
                    if (
                        cleaned := _clean_node(
                            child, mark=key == "marks", depth=depth + 1
                        )
                    )
                    is not None
                ]
    return result


def _serialize_document(document: dict) -> str:
    cleaned = _clean_node(document)
    cleaned["ara_format"] = FORMAT
    return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))


def sanitize_article_content(content: str, *, sanitize_html: bool = True) -> str:
    document = _parse_document(content)
    if document is not None:
        # Text is already plain text in TipTap. Escaping or linkifying the JSON
        # would change its meaning and can even invalidate its string syntax.
        return _serialize_document(document)
    return sanitize(content) if sanitize_html else content


class _LegacyLinkRepair(HTMLParser):
    """Remove anchors injected by bleach.linkify, without decoding JSON syntax."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            self.parts.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag != "a":
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")


def _decode_legacy_values(node: dict, depth: int = 0) -> dict:
    if depth > 100:
        return {}
    result = dict(node)
    if isinstance(node.get("text"), str):
        result["text"] = html.unescape(node["text"])
    if isinstance(node.get("attrs"), dict):
        result["attrs"] = {
            key: html.unescape(value) if isinstance(value, str) else value
            for key, value in node["attrs"].items()
        }
    for key in ("content", "marks"):
        if isinstance(node.get(key), list):
            result[key] = [
                _decode_legacy_values(child, depth + 1)
                for child in node[key]
                if isinstance(child, dict)
            ]
    return result


def normalize_stored_content(content: str) -> str:
    """Adapt pre-versioned, HTML-sanitized JSON only when reading stored data.

    Old storage lost the distinction between a literal '&lt;' and '<'. We can
    restore HTML semantics for legacy rows, but cannot recover that distinction.
    Versioned documents never undergo HTML entity decoding.
    """
    document = _parse_document(content)
    if document is None and content.lstrip().startswith("{"):
        repair = _LegacyLinkRepair()
        repair.feed(content)
        repair.close()
        document = _parse_document("".join(repair.parts))
    if document is None or document.get("ara_format") == FORMAT:
        return content
    return _serialize_document(_decode_legacy_values(document))
