"""Shared pytest fixtures and test-time settings tweaks."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _test_settings(settings, tmp_path):
    """Make tasks run inline and keep media files in a throwaway temp dir."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_image():
    """Return a factory that builds a tiny in-memory PNG upload."""
    from PIL import Image

    def _make(name="test.png"):
        buffer = io.BytesIO()
        Image.new("RGB", (10, 10), color="blue").save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile(name, buffer.read(), content_type="image/png")

    return _make
