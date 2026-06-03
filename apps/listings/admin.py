from django.contrib import admin
from django.utils.html import format_html

from apps.listings.models import Listing, ListingImage, ListingStatus
from apps.listings.tasks import notify_listing_status_change


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ("preview", "image", "caption", "is_primary", "order")
    readonly_fields = ("preview",)

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:4px;" />', obj.image.url
            )
        return "—"


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    inlines = [ListingImageInline]
    list_display = (
        "title",
        "city",
        "property_type",
        "monthly_rent",
        "owner_email",
        "status_badge",
        "is_available",
        "views_count",
        "created_at",
    )
    list_filter = ("status", "property_type", "is_available", "city", "created_at")
    search_fields = ("title", "description", "city", "address_line", "owner__email")
    readonly_fields = ("slug", "views_count", "published_at", "created_at", "updated_at")
    autocomplete_fields = ("owner",)
    date_hierarchy = "created_at"
    list_per_page = 25
    actions = ("approve_listings", "reject_listings", "mark_unavailable")

    fieldsets = (
        ("Ownership", {"fields": ("owner",)}),
        (
            "Details",
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "property_type",
                    ("monthly_rent", "deposit"),
                    ("bedrooms", "bathrooms", "area_sqft"),
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "address_line",
                    ("city", "state"),
                    ("country", "postal_code"),
                    ("latitude", "longitude"),
                )
            },
        ),
        (
            "Moderation & availability",
            {
                "fields": (
                    "status",
                    "rejection_reason",
                    "is_available",
                    "available_from",
                    "published_at",
                )
            },
        ),
        ("Metrics", {"fields": ("views_count", "created_at", "updated_at")}),
    )

    @admin.display(description="Owner", ordering="owner__email")
    def owner_email(self, obj):
        return obj.owner.email

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            ListingStatus.PUBLISHED: "#16a34a",
            ListingStatus.PENDING: "#d97706",
            ListingStatus.REJECTED: "#dc2626",
            ListingStatus.DRAFT: "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="Approve & publish selected listings")
    def approve_listings(self, request, queryset):
        count = 0
        for listing in queryset:
            listing.mark_published()
            notify_listing_status_change.delay(listing.id)
            count += 1
        self.message_user(request, f"Published {count} listing(s).")

    @admin.action(description="Reject selected listings")
    def reject_listings(self, request, queryset):
        updated = queryset.update(status=ListingStatus.REJECTED)
        for listing in queryset:
            notify_listing_status_change.delay(listing.id)
        self.message_user(request, f"Rejected {updated} listing(s).")

    @admin.action(description="Mark selected as unavailable")
    def mark_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f"Marked {updated} listing(s) unavailable.")


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ("id", "listing", "is_primary", "order", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("listing__title",)


admin.site.site_header = "Renter Administration"
admin.site.site_title = "Renter Admin"
admin.site.index_title = "Rental platform dashboard"
