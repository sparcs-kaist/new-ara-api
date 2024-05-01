"""
WSGI config for ara project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from starlette.middleware.cors import CORSMiddleware

from ara.controller.api import api_router

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ara.settings")

application = get_wsgi_application()


def get_fastapi() -> FastAPI:
    api = FastAPI(title="ARA")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # #################################################################################
    # https://fastapi.tiangolo.com/deployment/server-workers/
    # Nevertheless, as of now, Uvicorn's capabilities for handling worker processes
    # are more limited than Gunicorn's.
    # So, if you want to have a process manager at this level (at the Python level),
    # then it might be better to try with Gunicorn as the process manager.
    # ##################################################################################

    api.include_router(api_router, prefix="/v2")
    api.mount("/django", WSGIMiddleware(application))

    return api


app = get_fastapi()
