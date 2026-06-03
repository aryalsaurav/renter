#!/usr/bin/env bash
#
# Start the LOCAL development stack.
# Builds images, then runs web + worker + beat + postgres + redis.
# Migrations run automatically inside the django container's start.sh.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "No .env found — copying from .env.example. Edit it as needed."
    cp .env.example .env
fi

echo "Building local images..."
docker compose -f docker-compose.local.yml build

echo "Starting local stack at http://localhost:8000 ..."
docker compose -f docker-compose.local.yml up "$@"
