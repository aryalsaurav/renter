import pytest

from apps.listings.models import Listing, ListingStatus
from apps.listings.tests.factories import ListingFactory, PendingListingFactory

pytestmark = pytest.mark.django_db


def test_slug_is_generated_and_unique():
    a = ListingFactory(title="Same Title Here")
    b = ListingFactory(title="Same Title Here")
    assert a.slug
    assert a.slug != b.slug


def test_published_queryset_excludes_pending_and_unavailable():
    published = ListingFactory(status=ListingStatus.PUBLISHED, is_available=True)
    PendingListingFactory()
    ListingFactory(status=ListingStatus.PUBLISHED, is_available=False)

    qs = Listing.objects.published()
    assert published in qs
    assert qs.count() == 1


def test_mark_published_sets_timestamp():
    listing = PendingListingFactory()
    assert listing.published_at is None
    listing.mark_published()
    listing.refresh_from_db()
    assert listing.status == ListingStatus.PUBLISHED
    assert listing.published_at is not None


def test_location_summary_and_is_public():
    listing = ListingFactory(city="Denver", state="CO", country="USA")
    assert listing.location_summary == "Denver, CO, USA"
    assert listing.is_public is True
