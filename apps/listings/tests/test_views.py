import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory, VerifiedUserFactory
from apps.listings.models import Listing, ListingStatus
from apps.listings.tests.factories import ListingFactory, PendingListingFactory

pytestmark = pytest.mark.django_db


def test_public_list_page_renders(client):
    ListingFactory(status=ListingStatus.PUBLISHED, title="Public sunny flat")
    resp = client.get(reverse("listings:list"))
    assert resp.status_code == 200
    assert b"Public sunny flat" in resp.content


def test_detail_hides_owner_contact_for_anonymous(client):
    listing = ListingFactory(status=ListingStatus.PUBLISHED)
    resp = client.get(reverse("listings:detail", kwargs={"slug": listing.slug}))
    assert resp.status_code == 200
    assert b"Log in to view" in resp.content
    assert listing.owner.email.encode() not in resp.content


def test_detail_shows_owner_contact_when_logged_in(client):
    listing = ListingFactory(status=ListingStatus.PUBLISHED)
    user = UserFactory(password="pass12345!")
    client.force_login(user)
    resp = client.get(reverse("listings:detail", kwargs={"slug": listing.slug}))
    assert resp.status_code == 200
    assert listing.owner.email.encode() in resp.content


def test_create_requires_login(client):
    resp = client.get(reverse("listings:create"))
    assert resp.status_code == 302
    assert reverse("accounts:login") in resp.url


def test_pending_listing_not_visible_to_strangers(client):
    listing = PendingListingFactory()
    resp = client.get(reverse("listings:detail", kwargs={"slug": listing.slug}))
    assert resp.status_code == 404


def test_owner_can_view_own_pending_listing(client):
    owner = UserFactory()
    listing = PendingListingFactory(owner=owner)
    client.force_login(owner)
    resp = client.get(reverse("listings:detail", kwargs={"slug": listing.slug}))
    assert resp.status_code == 200


def test_owner_cannot_edit_others_listing(client):
    listing = ListingFactory()
    intruder = UserFactory()
    client.force_login(intruder)
    resp = client.get(reverse("listings:update", kwargs={"slug": listing.slug}))
    assert resp.status_code == 404


def test_image_upload_via_api(api_client, sample_image):
    from rest_framework_simplejwt.tokens import RefreshToken

    owner = VerifiedUserFactory()
    listing = ListingFactory(owner=owner, status=ListingStatus.PUBLISHED)
    token = RefreshToken.for_user(owner).access_token
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.post(
        reverse("listing-images", kwargs={"slug": listing.slug}),
        {"image": sample_image()},
        format="multipart",
    )
    assert resp.status_code == 201, resp.data
    assert listing.images.count() == 1
