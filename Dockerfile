FROM python:3.12-slim

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

RUN chmod +x entrypoint.sh
ENTRYPOINT [ "/app/entrypoint.sh" ]
