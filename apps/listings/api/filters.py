import django_filters

from apps.listings.models import Listing, PropertyType


class ListingFilter(django_filters.FilterSet):
    min_rent = django_filters.NumberFilter(field_name="monthly_rent", lookup_expr="gte")
    max_rent = django_filters.NumberFilter(field_name="monthly_rent", lookup_expr="lte")
    min_bedrooms = django_filters.NumberFilter(field_name="bedrooms", lookup_expr="gte")
    city = django_filters.CharFilter(field_name="city", lookup_expr="icontains")
    property_type = django_filters.ChoiceFilter(choices=PropertyType.choices)

    class Meta:
        model = Listing
        fields = ["city", "property_type", "bedrooms", "min_rent", "max_rent"]
