#!/bin/bash
# Wait for Postgres, then exec the container command.
# NOTE: this entrypoint intentionally does NOT run migrations (see start.sh).
set -o errexit
set -o pipefail
set -o nounset

python << 'END'
import sys
import time

import psycopg2

from os import environ

start = time.time()
while True:
    try:
        psycopg2.connect(
            dbname=environ["POSTGRES_DB"],
            user=environ["POSTGRES_USER"],
            password=environ["POSTGRES_PASSWORD"],
            host=environ["POSTGRES_HOST"],
            port=environ.get("POSTGRES_PORT", "5432"),
        )
        break
    except psycopg2.OperationalError as error:
        elapsed = int(time.time() - start)
        sys.stderr.write(f"Waiting for PostgreSQL ({elapsed}s)... {error}\n")
        time.sleep(2)
print("PostgreSQL is available.")
END

exec "$@"
