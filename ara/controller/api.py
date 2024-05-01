from ninja import NinjaAPI
from ninja.errors import ValidationError
from ratelimit.exception import RateLimitException

from ara.common.exceptions.ara_exception import (
    InvalidRequestException,
    TooManyRequestException,
)
from ara.controller.constants import HttpStatusCode
from ara.controller.ping import router as ping_router
from ara.controller.response import AraErrorResponseBody
from ara.settings import env

docs_url = None if env("DJANGO_ENV") == "production" else "/docs"
api = NinjaAPI(docs_url=docs_url)


@api.exception_handler(RateLimitException)
def too_many_requests(request, exception):
    return api.create_response(
        request,
        AraErrorResponseBody(TooManyRequestException()),
        status=HttpStatusCode.TOO_MANY_REQUESTS,
    )


@api.exception_handler(ValidationError)
def invalid_request(request, exception):
    return api.create_response(
        request,
        AraErrorResponseBody(InvalidRequestException()),
        status=HttpStatusCode.BAD_REQUEST,
    )


api.add_router("/ping", ping_router)
