#!/bin/bash
# Local web process: make/apply migrations then run the dev server with autoreload.
set -o errexit
set -o pipefail
set -o nounset

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput || true

# Create a default superuser if env vars are provided and it doesn't exist yet.
python manage.py shell << 'END' || true
import os
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
if email and password and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f"Created superuser {email}")
END

exec python manage.py runserver 0.0.0.0:8001
