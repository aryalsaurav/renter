FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    python3-dev \
    libpq-dev \
    postgresql-client \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip poetry

COPY . /app/

RUN poetry config virtualenvs.create false

RUN poetry install --no-root --with dev,prod


FROM python:3.12-slim 

WORKDIR /app
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
    
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN chmod +x docker/scripts/prod-entrypoint.sh
ENTRYPOINT [ "/app/docker/scripts/prod-entrypoint.sh" ]
