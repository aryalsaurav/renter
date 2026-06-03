#!/usr/bin/env bash
#
# Apply database migrations in PRODUCTION as a controlled, separate step.
# Run this during a release window — NOT on every container start.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running production migrations..."
docker compose -f docker-compose.prod.yml run --rm django python manage.py migrate --noinput

echo "Migrations complete."
