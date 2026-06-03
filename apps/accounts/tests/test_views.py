import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Profile
from apps.accounts.tests.factories import UserFactory

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_signup_creates_user_and_profile(client):
    resp = client.post(
        reverse("accounts:signup"),
        {
            "email": "fresh@example.com",
            "first_name": "Fresh",
            "last_name": "User",
            "password1": "strongpass123!",
            "password2": "strongpass123!",
        },
    )
    assert resp.status_code == 302
    user = User.objects.get(email="fresh@example.com")
    assert Profile.objects.filter(user=user).exists()


def test_login_and_logout_flow(client):
    UserFactory(email="member@example.com", password="strongpass123!")
    resp = client.post(
        reverse("accounts:login"),
        {"username": "member@example.com", "password": "strongpass123!"},
    )
    assert resp.status_code == 302
    # Profile page now reachable.
    assert client.get(reverse("accounts:profile")).status_code == 200


def test_profile_requires_login(client):
    resp = client.get(reverse("accounts:profile"))
    assert resp.status_code == 302
    assert reverse("accounts:login") in resp.url


def test_profile_auto_created_signal():
    user = UserFactory()
    assert hasattr(user, "profile")
