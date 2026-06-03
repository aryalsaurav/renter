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

echo "Starting command: $@"

exec "$@"