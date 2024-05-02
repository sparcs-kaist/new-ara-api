from fastapi import APIRouter

from ara.controller.sample import router as sample_router
from ara.controller.sample.sample_controller import test_router

fastapi_router = APIRouter()

fastapi_router.include_router(sample_router, prefix="/api")
fastapi_router.include_router(test_router, prefix="/api")
