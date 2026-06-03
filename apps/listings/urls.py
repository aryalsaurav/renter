from django.urls import path

from apps.listings import views

app_name = "listings"

urlpatterns = [
    path("", views.listing_list, name="list"),
    path("my/listings/", views.my_listings, name="my-listings"),
    path("listings/new/", views.listing_create, name="create"),
    path("listings/<slug:slug>/", views.listing_detail, name="detail"),
    path("listings/<slug:slug>/edit/", views.listing_update, name="update"),
    path("listings/<slug:slug>/delete/", views.listing_delete, name="delete"),
]
