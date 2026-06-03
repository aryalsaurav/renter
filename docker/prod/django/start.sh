#!/bin/bash
# Production web process.
#
# IMPORTANT: database migrations are deliberately NOT run here. Run them as a
# separate, controlled release step, e.g.:
#   docker compose -f docker-compose.prod.yml run --rm django python manage.py migrate
set -o errexit
set -o pipefail
set -o nounset

# Collect static files (served by WhiteNoise). This is not a DB migration.
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
