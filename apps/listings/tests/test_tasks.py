import pytest
from django.core import mail
from django.utils import timezone

from apps.listings.models import ListingStatus
from apps.listings.tasks import (
    daily_listing_digest,
    deactivate_stale_pending_listings,
    notify_new_listing,
    notify_listing_status_change,
)
from apps.listings.tests.factories import ListingFactory, PendingListingFactory

pytestmark = pytest.mark.django_db


def test_notify_new_listing_emails_moderators(settings):
    listing = PendingListingFactory()
    notify_new_listing(listing.id)
    assert len(mail.outbox) == 1
    assert settings.LISTING_MODERATION_EMAIL in mail.outbox[0].to


def test_notify_status_change_emails_owner_on_publish():
    listing = ListingFactory(status=ListingStatus.PUBLISHED)
    notify_listing_status_change(listing.id)
    assert len(mail.outbox) == 1
    assert listing.owner.email in mail.outbox[0].to


def test_deactivate_stale_pending_listings():
    stale = PendingListingFactory()
    # Force created_at into the past (auto_now_add must be bypassed via update).
    type(stale).objects.filter(pk=stale.pk).update(
        created_at=timezone.now() - timezone.timedelta(days=40)
    )
    PendingListingFactory()  # recent, should be untouched

    count = deactivate_stale_pending_listings(days=30)
    stale.refresh_from_db()
    assert count == 1
    assert stale.status == ListingStatus.REJECTED


def test_daily_digest_counts_published():
    ListingFactory(status=ListingStatus.PUBLISHED)
    ListingFactory(status=ListingStatus.PUBLISHED)
    PendingListingFactory()
    assert daily_listing_digest() == 2
