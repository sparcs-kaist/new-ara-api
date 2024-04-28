from typing import Any

from pydantic import BaseModel


class PaginatedData(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[Any]


class NesAraPagination:
    pass
