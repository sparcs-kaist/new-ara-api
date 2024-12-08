from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def api():
    return {"api": "api"}


test_router = APIRouter(prefix="/test")


@router.get("/")
def test():
    return {"test": "test"}
