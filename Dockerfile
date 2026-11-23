# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.13.9 AS uv

FROM python:3.14.7-slim-bookworm AS base

ENV PATH="/newara/www/.venv/bin:$PATH" \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gettext libmariadb3 netcat-openbsd supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /newara/www
COPY --from=uv /uv /uvx /usr/local/bin/

FROM base AS dependencies

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM base AS application

COPY --from=dependencies /newara/www/.venv /newara/www/.venv
COPY . .
RUN mkdir -p /var/log/newara \
    && chmod +x .docker/run.sh .docker/run-celery.sh

EXPOSE 9000 9001
ENTRYPOINT ["/newara/www/.docker/run.sh"]

FROM application AS development
ENV DJANGO_ENV=development
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

FROM application AS test
ENV DJANGO_ENV=development DJANGO_SETTINGS_MODULE=ara.settings.test FCM_DISABLED=1
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --group test

FROM application AS production
ENV DJANGO_ENV=production
