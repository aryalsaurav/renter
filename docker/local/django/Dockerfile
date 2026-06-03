# Local development image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# System deps (build tools for any sdists, libpq + image libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --with dev --no-root

# Project scripts
COPY ./docker/local/django/entrypoint.sh /entrypoint.sh
COPY ./docker/local/django/start.sh /start.sh
COPY ./docker/local/django/celery/worker/start.sh /start-celeryworker.sh
COPY ./docker/local/django/celery/beat/start.sh /start-celerybeat.sh
RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh \
    && chmod +x /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh

COPY . /app

ENTRYPOINT ["/entrypoint.sh"]
