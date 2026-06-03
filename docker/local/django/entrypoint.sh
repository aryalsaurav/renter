#!/bin/bash
# Wait for Postgres and Redis to be ready, then exec the container command.
set -o errexit
set -o pipefail
set -o nounset

python << 'END'
import sys
import time

import psycopg2

from os import environ

suggest_unrecoverable_after = 30
start = time.time()
while True:
    try:
        psycopg2.connect(
            dbname=environ.get("POSTGRES_DB", "renter"),
            user=environ.get("POSTGRES_USER", "renter"),
            password=environ.get("POSTGRES_PASSWORD", "renter"),
            host=environ.get("POSTGRES_HOST", "postgres"),
            port=environ.get("POSTGRES_PORT", "5432"),
        )
        break
    except psycopg2.OperationalError as error:
        elapsed = int(time.time() - start)
        sys.stderr.write(f"Waiting for PostgreSQL ({elapsed}s)...\n")
        if elapsed > suggest_unrecoverable_after:
            sys.stderr.write(f"  Still can't reach PostgreSQL: {error}\n")
        time.sleep(2)
print("PostgreSQL is available.")
END

exec "$@"
