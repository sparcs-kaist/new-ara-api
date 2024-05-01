from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def test():
    return {"test": "test"}


auth_router = APIRouter()
