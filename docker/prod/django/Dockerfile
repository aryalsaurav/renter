# Production image — multi-stage build with Poetry exporting to a venv.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
# Dependency selection is configurable so the SAME image can be built for tests.
# Defaults to main + prod groups (no dev/test tooling). For a test image pass:
#   --build-arg POETRY_INSTALL_ARGS="--only main,prod,dev"
ARG POETRY_INSTALL_ARGS="--only main,prod"
RUN poetry install ${POETRY_INSTALL_ARGS} --no-root


# ---- Final runtime image ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user.
RUN groupadd -r django && useradd -r -g django django

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

COPY ./docker/prod/django/entrypoint.sh /entrypoint.sh
COPY ./docker/prod/django/start.sh /start.sh
COPY ./docker/prod/django/celery/worker/start.sh /start-celeryworker.sh
COPY ./docker/prod/django/celery/beat/start.sh /start-celerybeat.sh
RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh \
    && chmod +x /entrypoint.sh /start.sh /start-celeryworker.sh /start-celerybeat.sh

COPY . /app
RUN chown -R django:django /app

USER django

ENTRYPOINT ["/entrypoint.sh"]
