import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory, VerifiedUserFactory
from apps.listings.models import Listing, ListingStatus
from apps.listings.tests.factories import ListingFactory, PendingListingFactory

pytestmark = pytest.mark.django_db


def auth(client, user):
    """Attach a JWT access token for `user` to the API client."""
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


class TestPublicBrowsing:
    def test_anonymous_can_list_published_listings(self, api_client):
        ListingFactory(status=ListingStatus.PUBLISHED)
        PendingListingFactory()
        resp = api_client.get(reverse("listing-list"))
        assert resp.status_code == 200
        assert resp.data["count"] == 1

    def test_anonymous_cannot_see_owner_contact(self, api_client):
        listing = ListingFactory(status=ListingStatus.PUBLISHED)
        resp = api_client.get(
            reverse("listing-detail", kwargs={"slug": listing.slug})
        )
        assert resp.status_code == 200
        # Photos + location visible, but owner contact hidden.
        assert resp.data["city"] == listing.city
        assert resp.data["owner_contact"] is None

    def test_authenticated_user_sees_owner_contact(self, api_client):
        listing = ListingFactory(status=ListingStatus.PUBLISHED)
        viewer = UserFactory()
        auth(api_client, viewer)
        resp = api_client.get(
            reverse("listing-detail", kwargs={"slug": listing.slug})
        )
        assert resp.status_code == 200
        assert resp.data["owner_contact"]["email"] == listing.owner.email

    def test_anonymous_cannot_open_pending_listing(self, api_client):
        listing = PendingListingFactory()
        resp = api_client.get(
            reverse("listing-detail", kwargs={"slug": listing.slug})
        )
        assert resp.status_code == 404


class TestListingWrites:
    def test_anonymous_cannot_create(self, api_client):
        resp = api_client.post(reverse("listing-list"), {"title": "x"})
        assert resp.status_code in (401, 403)

    def test_unverified_user_create_goes_to_pending(self, api_client):
        user = UserFactory(is_verified=False)
        auth(api_client, user)
        payload = {
            "title": "Bright studio downtown",
            "description": "Nice and sunny apartment in the center of town.",
            "property_type": "studio",
            "monthly_rent": "950.00",
            "deposit": "900.00",
            "bedrooms": 1,
            "bathrooms": 1,
            "address_line": "5 Center Rd",
            "city": "Metropolis",
            "country": "USA",
            "available_from": "2030-01-01",
        }
        resp = api_client.post(reverse("listing-list"), payload)
        assert resp.status_code == 201, resp.data
        listing = Listing.objects.get(id=resp.data["id"])
        assert listing.status == ListingStatus.PENDING
        assert listing.owner == user

    def test_verified_user_create_is_published(self, api_client):
        user = VerifiedUserFactory()
        auth(api_client, user)
        payload = {
            "title": "Verified owner listing",
            "description": "A great place from a trusted owner, ready to move in.",
            "property_type": "house",
            "monthly_rent": "2000.00",
            "bedrooms": 3,
            "bathrooms": 2,
            "address_line": "9 Trust Ave",
            "city": "Trustville",
            "country": "USA",
            "available_from": "2030-01-01",
        }
        resp = api_client.post(reverse("listing-list"), payload)
        assert resp.status_code == 201, resp.data
        assert Listing.objects.get(id=resp.data["id"]).status == (
            ListingStatus.PUBLISHED
        )

    def test_rejects_zero_rent(self, api_client):
        user = UserFactory()
        auth(api_client, user)
        payload = {
            "title": "Invalid rent listing",
            "description": "This listing has an invalid rent value for testing.",
            "property_type": "room",
            "monthly_rent": "0",
            "bedrooms": 1,
            "bathrooms": 1,
            "address_line": "1 Nowhere",
            "city": "Nowhere",
            "country": "USA",
            "available_from": "2030-01-01",
        }
        resp = api_client.post(reverse("listing-list"), payload)
        assert resp.status_code == 400
        assert "monthly_rent" in resp.data

    def test_user_cannot_edit_others_listing(self, api_client):
        listing = ListingFactory(status=ListingStatus.PUBLISHED)
        other = UserFactory()
        auth(api_client, other)
        resp = api_client.patch(
            reverse("listing-detail", kwargs={"slug": listing.slug}),
            {"title": "Hijacked title here"},
        )
        assert resp.status_code in (403, 404)

    def test_owner_can_edit_own_listing(self, api_client):
        owner = UserFactory()
        listing = ListingFactory(owner=owner, status=ListingStatus.PUBLISHED)
        auth(api_client, owner)
        resp = api_client.patch(
            reverse("listing-detail", kwargs={"slug": listing.slug}),
            {"title": "Updated title goes here"},
        )
        assert resp.status_code == 200
        listing.refresh_from_db()
        assert listing.title == "Updated title goes here"

    def test_mine_endpoint_returns_only_own_listings(self, api_client):
        owner = UserFactory()
        ListingFactory(owner=owner, status=ListingStatus.PENDING)
        ListingFactory()  # someone else's
        auth(api_client, owner)
        resp = api_client.get(reverse("listing-mine"))
        assert resp.status_code == 200
        results = resp.data["results"] if "results" in resp.data else resp.data
        assert len(results) == 1


class TestJWTAuth:
    def test_obtain_token_with_valid_credentials(self, api_client):
        UserFactory(email="login@example.com", password="strongpass123!")
        resp = api_client.post(
            reverse("token_obtain_pair"),
            {"email": "login@example.com", "password": "strongpass123!"},
        )
        assert resp.status_code == 200
        assert "access" in resp.data and "refresh" in resp.data

    def test_register_creates_account(self, api_client):
        resp = api_client.post(
            reverse("api-register"),
            {
                "email": "newbie@example.com",
                "password": "strongpass123!",
                "password2": "strongpass123!",
                "first_name": "New",
            },
        )
        assert resp.status_code == 201
        assert resp.data["email"] == "newbie@example.com"
