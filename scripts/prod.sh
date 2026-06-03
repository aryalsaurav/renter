#!/usr/bin/env bash
#
# Start the PRODUCTION stack.
#
# This script does NOT run database migrations. Migrations must be applied as a
# deliberate, separate release step using scripts/migrate_prod.sh.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env.prod ]; then
    echo "ERROR: .env.prod not found. Create it from .env.prod.sample.txt first." >&2
    exit 1
fi

echo "Building production images..."
docker compose -f docker-compose.prod.yml build

echo "Starting production stack (no migrations will run)..."
docker compose -f docker-compose.prod.yml up -d "$@"

echo
echo "Stack is up. Reminder: run migrations separately with:"
echo "    ./scripts/migrate_prod.sh"
