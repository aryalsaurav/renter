#!/usr/bin/env bash
#
# Create a superuser in PRODUCTION (interactive).
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose -f docker-compose.prod.yml run --rm django python manage.py createsuperuser
