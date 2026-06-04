#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

until pg_isready \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER"
do
  echo "Postgres unavailable..."
  sleep 2
done

echo "PostgreSQL is ready."

# Run migrations ONLY for web container
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput

    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting command: $@"

exec "$@"