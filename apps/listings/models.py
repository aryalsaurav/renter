from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class PropertyType(models.TextChoices):
    APARTMENT = "apartment", "Apartment"
    HOUSE = "house", "House"
    ROOM = "room", "Room"
    STUDIO = "studio", "Studio"
    CONDO = "condo", "Condo"
    OTHER = "other", "Other"


class ListingStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending review"
    PUBLISHED = "published", "Published"
    REJECTED = "rejected", "Rejected"


class ListingQuerySet(models.QuerySet):
    def published(self):
        """Listings the public is allowed to browse."""
        return self.filter(status=ListingStatus.PUBLISHED, is_available=True)

    def for_owner(self, user):
        return self.filter(owner=user)


class Listing(models.Model):
    """A rental property listing.

    Public visitors only ever see *published & available* listings, and even
    then the owner's contact details are hidden (see the API serializers /
    templates). Owner contact is exposed only to authenticated users.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, default=PropertyType.APARTMENT
    )

    # --- Pricing & specs (validated) ---
    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Monthly rent amount.",
    )
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    bedrooms = models.PositiveSmallIntegerField(default=1)
    bathrooms = models.PositiveSmallIntegerField(default=1)
    area_sqft = models.PositiveIntegerField(
        null=True, blank=True, help_text="Floor area in square feet."
    )

    # --- Location (public) ---
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=120, db_index=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, default="")
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # --- Availability & moderation ---
    is_available = models.BooleanField(default=True)
    available_from = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=20, choices=ListingStatus.choices, default=ListingStatus.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ListingQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "is_available"]),
            models.Index(fields=["city", "property_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        if self.status == ListingStatus.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def _build_unique_slug(self):
        base = slugify(self.title)[:200] or "listing"
        slug = base
        i = 1
        Model = type(self)
        while Model.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            i += 1
            slug = f"{base}-{i}"
        return slug

    def get_absolute_url(self):
        return reverse("listings:detail", kwargs={"slug": self.slug})

    @property
    def is_public(self):
        return self.status == ListingStatus.PUBLISHED and self.is_available

    @property
    def location_summary(self):
        parts = [self.city, self.state, self.country]
        return ", ".join(p for p in parts if p)

    def mark_published(self):
        self.status = ListingStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="listings/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_primary", "order", "id")

    def __str__(self):
        return f"Image<{self.listing_id}>"
