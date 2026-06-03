"""Test settings: eager Celery, local-memory email.

By default the database is fast in-memory sqlite (great for `poetry run pytest`
locally). In CI we run against the real PostgreSQL service from
docker-compose.test.yml — set ``USE_POSTGRES_FOR_TESTS=True`` to switch.

Run with:  pytest --ds=config.settings.test
"""
from .base import *  # noqa: F401,F403
from .base import DATABASES, env  # noqa: F401

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
SECRET_KEY = "test-secret-key-that-is-sufficiently-long-for-hmac-sha256-signing"

if not env.bool("USE_POSTGRES_FOR_TESTS", default=False):
    # Fast, dependency-free local test database.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
# else: inherit the PostgreSQL config from base.py (driven by POSTGRES_* env).

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
