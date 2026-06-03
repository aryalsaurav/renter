from django.db.models import F, Q
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.listings.api.filters import ListingFilter
from apps.listings.api.permissions import IsOwnerOrReadOnly
from apps.listings.api.serializers import (
    ListingImageSerializer,
    ListingSerializer,
    ListingWriteSerializer,
)
from apps.listings.models import Listing, ListingImage, ListingStatus
from apps.listings.tasks import notify_new_listing


class ListingViewSet(viewsets.ModelViewSet):
    """Public read access (published listings only); owners manage their own.

    - Anonymous & all users: list/retrieve published+available listings.
      Owner contact details are hidden for anonymous users (handled in serializer).
    - Authenticated users: create listings.
    - Owners: update/delete their own listings, and see them in `mine`.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filterset_class = ListingFilter
    search_fields = ("title", "description", "city", "address_line")
    ordering_fields = ("monthly_rent", "created_at", "bedrooms", "views_count")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ListingWriteSerializer
        return ListingSerializer

    def get_queryset(self):
        base = Listing.objects.select_related("owner").prefetch_related("images")
        user = self.request.user
        # Owners managing their listings (mine / writes) see all their own.
        if self.action in ("update", "partial_update", "destroy", "mine"):
            if user.is_authenticated:
                return base.for_owner(user)
            return base.none()
        # Authenticated users can browse published listings plus their own.
        if user.is_authenticated:
            return base.filter(
                Q(status=ListingStatus.PUBLISHED, is_available=True) | Q(owner=user)
            ).distinct()
        return base.published()

    def perform_create(self, serializer):
        listing = serializer.save()
        if not listing.owner.is_verified:
            notify_new_listing.delay(listing.id)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Count a view only for public, non-owner hits.
        if instance.owner_id != getattr(request.user, "id", None):
            Listing.objects.filter(pk=instance.pk).update(
                views_count=F("views_count") + 1
            )
            instance.refresh_from_db(fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def mine(self, request):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        serializer = ListingSerializer(
            page if page is not None else qs, many=True, context={"request": request}
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsOwnerOrReadOnly],
    )
    def images(self, request, slug=None):
        """Upload an image to an existing listing the caller owns."""
        listing = self.get_object()
        serializer = ListingImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(listing=listing)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ListingImageViewSet(mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Delete individual images (owner only)."""

    queryset = ListingImage.objects.select_related("listing")
    serializer_class = ListingImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
