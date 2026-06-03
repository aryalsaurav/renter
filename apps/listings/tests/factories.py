import factory

from apps.accounts.tests.factories import UserFactory
from apps.listings.models import Listing, ListingStatus, PropertyType


class ListingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Listing

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Cozy place number {n}")
    description = "A lovely place to stay with great light and a quiet street."
    property_type = PropertyType.APARTMENT
    monthly_rent = 1200
    deposit = 1000
    bedrooms = 2
    bathrooms = 1
    address_line = "123 Main St"
    city = "Springfield"
    state = "IL"
    country = "USA"
    status = ListingStatus.PUBLISHED


class PendingListingFactory(ListingFactory):
    status = ListingStatus.PENDING
