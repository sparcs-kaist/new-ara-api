from ara.controller.constants import HttpStatusCode


class AraException(Exception):
    error_code: int | None
    error_reason: str | None


class TooManyRequestException(AraException):
    """too many requests exception"""

    error_code = HttpStatusCode.TOO_MANY_REQUESTS
    error_reason = "Too many requests"


class InvalidRequestException(AraException):
    """invalid request exception"""

    error_code = HttpStatusCode.BAD_REQUEST
    error_reason = "Invalid request"
