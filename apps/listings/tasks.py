"""Celery tasks for the listings app."""
import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def notify_new_listing(self, listing_id):
    """Email moderators when a new listing is submitted for review."""
    from apps.listings.models import Listing

    try:
        listing = Listing.objects.select_related("owner").get(pk=listing_id)
    except Listing.DoesNotExist:
        logger.warning("notify_new_listing: listing %s no longer exists", listing_id)
        return

    subject = f"[Renter] New listing pending review: {listing.title}"
    body = (
        f"A new listing was submitted by {listing.owner.email}.\n\n"
        f"Title: {listing.title}\n"
        f"City: {listing.city}\n"
        f"Rent: {listing.monthly_rent}\n"
        f"Status: {listing.get_status_display()}\n"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.LISTING_MODERATION_EMAIL],
        fail_silently=False,
    )
    logger.info("Sent new-listing notification for %s", listing_id)


@shared_task
def notify_listing_status_change(listing_id):
    """Email the owner when their listing is published or rejected."""
    from apps.listings.models import Listing, ListingStatus

    try:
        listing = Listing.objects.select_related("owner").get(pk=listing_id)
    except Listing.DoesNotExist:
        return

    if listing.status == ListingStatus.PUBLISHED:
        subject = f"[Renter] Your listing is live: {listing.title}"
        body = "Good news! Your listing has been approved and is now public."
    elif listing.status == ListingStatus.REJECTED:
        subject = f"[Renter] Your listing was not approved: {listing.title}"
        body = (
            "Unfortunately your listing was rejected.\n"
            f"Reason: {listing.rejection_reason or 'Not specified.'}"
        )
    else:
        return

    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [listing.owner.email],
        fail_silently=True,
    )


@shared_task
def deactivate_stale_pending_listings(days=30):
    """Celery-beat periodic task.

    Auto-reject listings stuck in 'pending' for longer than `days`.
    """
    from apps.listings.models import Listing, ListingStatus

    cutoff = timezone.now() - timezone.timedelta(days=days)
    stale = Listing.objects.filter(
        status=ListingStatus.PENDING, created_at__lt=cutoff
    )
    count = stale.update(
        status=ListingStatus.REJECTED,
        rejection_reason="Automatically rejected: pending review too long.",
    )
    logger.info("Auto-rejected %s stale pending listings", count)
    return count


@shared_task
def daily_listing_digest():
    """Celery-beat periodic task: log a daily count of published listings."""
    from apps.listings.models import Listing

    total = Listing.objects.published().count()
    logger.info("Daily digest: %s published listings available", total)
    return total
