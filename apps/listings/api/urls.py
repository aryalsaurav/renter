from rest_framework.routers import DefaultRouter

from apps.listings.api.views import ListingImageViewSet, ListingViewSet

router = DefaultRouter()
router.register("listings", ListingViewSet, basename="listing")
router.register("listing-images", ListingImageViewSet, basename="listing-image")

urlpatterns = router.urls
