from http import HTTPStatus
from typing import Any, NamedTuple

from pydantic import BaseModel


class AraResponse(NamedTuple):
    status_code: HTTPStatus
    data: Any


class AraErrorResponseBody(BaseModel):
    # necessary
    error_code: int | None
    error_reason: str = ""

    def __init__(self, exception: Exception):
        message = str(exception)
        # TODO: Create AraException and use error_code & error_reason
        data = {"message": message}
        super().__init__(**data)
