from typing import Any, Optional

from pydantic import BaseModel


class PaginatedData(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: list[Any]


class NesAraPagination:
    pass
