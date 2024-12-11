from django.http import HttpRequest
from ninja import Router

from ara.controller.authentication import AuthLoggedInUser
from ara.controller.constants import HttpStatusCode
from ara.controller.response import AraResponse

router = Router()


@router.get(
    "/",
    response={
        HttpStatusCode.OK: str,
        HttpStatusCode.INTERNAL_SERVER_ERROR: str,
    },
)
def ping(request: HttpRequest):
    return AraResponse(
        status_code=HttpStatusCode.OK,
        data="pong",
    )


auth_router = Router(auth=AuthLoggedInUser())


@auth_router.get(
    "/auth",
    response={
        HttpStatusCode.OK: str,
        HttpStatusCode.BAD_REQUEST: str,
    },
)
def auth_ping(request: HttpRequest):
    return AraResponse(
        status_code=HttpStatusCode.OK,
        data="pong",
    )
