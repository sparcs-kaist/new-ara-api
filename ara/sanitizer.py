from urllib.parse import urlparse

import bleach


def sanitize(content):
    def _allowed_attributes(tag, name, value):
        if name in ["src"]:
            p = urlparse(value)
            return (not p.netloc) or p.netloc.endswith(
                (
                    "sparcs.org",
                    "kaist.ac.kr",
                    "sparcs-newara.s3.amazonaws.com",
                    "sparcs-newara-dev.s3.amazonaws.com",
                )
            )

        if tag == "a":
            return name in ["href", "title", "data-bookmark"]
        if tag == "abbr":
            return (name in ["title"],)
        if tag == "acronym":
            return (name in ["title"],)
        if tag == "ol":
            return name in ["start"]
        if tag == "img":
            return name in ["width", "height", "alt", "title", "data-attachment"]
        if tag == "iframe":
            return name in ["width", "height", "allowfullscreen"]
        if tag == "video":
            return name in [
                "controls",
                "width",
                "height",
                "allowfullscreen",
                "preload",
                "poster",
            ]
        if tag == "audio":
            return name in ["controls", "preload"]

        return False

    allowed_tags = (
        bleach.ALLOWED_TAGS
        | {"p", "pre", "span", "h1", "h2", "h3", "br", "hr", "s", "u", "ol"}
        | {"img", "iframe", "video", "audio", "source"}
        | {
            "sub",
            "sup",
            "table",
            "tbody",
            "td",
            "tfoot",
            "th",
            "thead",
            "tr",
            "tt",
            "u",
            "ul",
        }
    )

    return bleach.clean(content, tags=allowed_tags, attributes=_allowed_attributes)
