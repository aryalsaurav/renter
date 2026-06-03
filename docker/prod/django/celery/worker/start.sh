#!/bin/bash
set -o errexit
set -o nounset

exec celery -A config worker --loglevel=info --concurrency "${CELERY_WORKER_CONCURRENCY:-4}"
