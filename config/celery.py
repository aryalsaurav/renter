"""Celery application definition."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("renter")

# All Celery config keys are namespaced with CELERY_ in Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py modules in installed apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
