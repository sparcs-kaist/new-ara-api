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
    """scoped article을 제외하는 lookup dict를 반환한다.
    `prefix`는 `Article` relation path이며 FK model에서는 `"article"`을 사용한다."""
    lookup = f"{prefix}__" if prefix else ""
    return {
        f"{lookup}related_course_group__isnull": True,
        f"{lookup}related_major__isnull": True,
    }


def exclude_scoped_articles(queryset, prefix: str = ""):
    """QuerySet에서 course/major article을 제외한다."""
    return queryset.filter(**general_article_filter(prefix))


def scoped_article_sql_condition(table: str = "`core_article`") -> str:
    """`WHERE`/`AND` 뒤에 붙일 scoped article 제외 raw SQL condition을 반환한다.
    `table`은 `core_article`의 table name 또는 alias다."""
    # ORM filter와 같은 columns를 사용한다. `related_course`는 source term이며
    # course board scope는 `related_course_group`이 결정한다.
    return (
        f"{table}.`related_course_group_id` IS NULL "
        f"AND {table}.`related_major_id` IS NULL"
    )
