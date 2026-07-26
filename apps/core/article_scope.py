"""과목/학과 게시판(scoped) 글을 일반 경로에서 제외하기 위한 단일 진입점.

과목·학과 글은 별도 테이블이 아니라 `core_article` 에 일반 글과 함께 저장되고
(related_course_group / related_major 로 구분), 접근 통제는 board mask 가 아니라
IsEnrolledInCourseGroup / IsSameMajor 가 담당한다. 그래서 "일반 게시판 글 목록"
을 만드는 모든 쿼리는 scoped 글을 명시적으로 빼야 한다.

이 규칙이 호출부마다 흩어져 있으면 Article 쿼리셋을 새로 만드는 코드가 자동으로
규칙 밖에 놓인다(= 위험한 쪽이 기본값). 필터 정의를 여기 한 곳에 모으고,
목록/검색/네비게이션 경로는 전부 이 모듈을 경유한다.

ORM 을 타지 않는 경로(raw SQL, Elasticsearch 색인)를 위해 SQL 조건 문자열도
같이 제공한다.
"""

from __future__ import annotations


def general_article_filter(prefix: str = "") -> dict:
    """scoped 글 제외 필터를 lookup dict 로 반환.

    prefix 는 Article 을 가리키는 관계 경로. Article 쿼리셋이면 "" (기본),
    ArticleReadLog/BestArticle 처럼 Article 을 FK 로 가진 모델이면 "article".
    """
    lookup = f"{prefix}__" if prefix else ""
    return {
        f"{lookup}related_course__isnull": True,
        f"{lookup}related_major__isnull": True,
    }


def exclude_scoped_articles(queryset, prefix: str = ""):
    """queryset 에서 과목/학과 게시판 글을 제외한다."""
    return queryset.filter(**general_article_filter(prefix))


def scoped_article_sql_condition(table: str = "`core_article`") -> str:
    """raw SQL 용 조건. WHERE / AND 뒤에 그대로 붙인다.

    table 은 core_article 을 가리키는 테이블명 또는 별칭 (백틱 포함).
    """
    # ORM 쪽 필터(related_course__isnull / related_major__isnull)와 같은 컬럼을
    # 봐야 두 경로의 판정이 어긋나지 않는다.
    return (
        f"{table}.`related_course_id` IS NULL "
        f"AND {table}.`related_major_id` IS NULL"
    )
