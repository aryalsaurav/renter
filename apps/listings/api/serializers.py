from rest_framework import serializers

from apps.listings.models import Listing, ListingImage, ListingStatus


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ("id", "image", "caption", "is_primary", "order")
        read_only_fields = ("id",)


class OwnerContactSerializer(serializers.Serializer):
    """Owner contact info — only ever serialized for authenticated requests."""

    id = serializers.IntegerField()
    display_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()


class ListingSerializer(serializers.ModelSerializer):
    """Read serializer.

    `owner_contact` is populated ONLY for authenticated requests; anonymous
    visitors get `null` so the owner's email/phone stays private. Everyone can
    still see photos and the location summary.
    """

    images = ListingImageSerializer(many=True, read_only=True)
    owner_contact = serializers.SerializerMethodField()
    location_summary = serializers.CharField(read_only=True)
    property_type_display = serializers.CharField(
        source="get_property_type_display", read_only=True
    )

    class Meta:
        model = Listing
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "property_type",
            "property_type_display",
            "monthly_rent",
            "deposit",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "address_line",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "location_summary",
            "is_available",
            "available_from",
            "status",
            "views_count",
            "images",
            "owner_contact",
            "created_at",
        )
        read_only_fields = fields

    def get_owner_contact(self, obj):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            return OwnerContactSerializer(
                {
                    "id": obj.owner_id,
                    "display_name": obj.owner.display_name,
                    "email": obj.owner.email,
                    "phone": obj.owner.phone,
                }
            ).data
        return None


class ListingWriteSerializer(serializers.ModelSerializer):
    """Create / update serializer for owners.

    Accepts an optional list of `uploaded_images` (multipart) on create.
    """

    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Listing
        fields = (
            "id",
            "title",
            "description",
            "property_type",
            "monthly_rent",
            "deposit",
            "bedrooms",
            "bathrooms",
            "area_sqft",
            "address_line",
            "city",
            "state",
            "country",
            "postal_code",
            "latitude",
            "longitude",
            "is_available",
            "available_from",
            "uploaded_images",
        )

    def validate_monthly_rent(self, value):
        if value <= 0:
            raise serializers.ValidationError("Monthly rent must be greater than zero.")
        return value

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value.strip()

    def validate(self, attrs):
        deposit = attrs.get("deposit", getattr(self.instance, "deposit", 0))
        rent = attrs.get("monthly_rent", getattr(self.instance, "monthly_rent", 0))
        if deposit and rent and deposit > rent * 12:
            raise serializers.ValidationError(
                {"deposit": "Deposit looks unrealistically high (> 12 months rent)."}
            )
        return attrs

    def create(self, validated_data):
        images = validated_data.pop("uploaded_images", [])
        owner = self.context["request"].user
        # Verified owners publish immediately; others go to moderation queue.
        validated_data["status"] = (
            ListingStatus.PUBLISHED if owner.is_verified else ListingStatus.PENDING
        )
        listing = Listing.objects.create(owner=owner, **validated_data)
        for idx, image in enumerate(images):
            ListingImage.objects.create(
                listing=listing, image=image, is_primary=(idx == 0), order=idx
            )
        return listing

    def update(self, instance, validated_data):
        images = validated_data.pop("uploaded_images", [])
        listing = super().update(instance, validated_data)
        for idx, image in enumerate(images):
            ListingImage.objects.create(listing=listing, image=image, order=idx)
        return listing
