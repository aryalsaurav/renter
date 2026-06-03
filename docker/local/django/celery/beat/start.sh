#!/bin/bash
set -o errexit
set -o nounset

# Remove a stale pid file if the container was killed uncleanly.
rm -f './celerybeat.pid'
exec celery -A config beat --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
