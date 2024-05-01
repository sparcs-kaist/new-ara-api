from fastapi import APIRouter

from ara.controller.sample import router as sample_router

api_router = APIRouter()

api_router.include_router(sample_router, prefix="/sample")
