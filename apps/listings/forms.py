from django import forms
from django.forms import modelformset_factory

from apps.listings.models import Listing, ListingImage


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = (
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
            "available_from",
            "is_available",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "available_from": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ("is_available",):
                continue
            css = field.widget.attrs.get("class", "")
            if "form-select" not in css and "form-control" not in css:
                widget = (
                    "form-select"
                    if isinstance(field.widget, forms.Select)
                    else "form-control"
                )
                field.widget.attrs["class"] = (css + " " + widget).strip()

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters.")
        return title

    def clean_monthly_rent(self):
        rent = self.cleaned_data["monthly_rent"]
        if rent <= 0:
            raise forms.ValidationError("Monthly rent must be greater than zero.")
        return rent

    def clean(self):
        cleaned = super().clean()
        deposit = cleaned.get("deposit") or 0
        rent = cleaned.get("monthly_rent") or 0
        if deposit and rent and deposit > rent * 12:
            self.add_error(
                "deposit", "Deposit looks unrealistically high (> 12 months rent)."
            )
        return cleaned


class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ("image", "caption", "is_primary")
        widgets = {
            "caption": forms.TextInput(attrs={"class": "form-control"}),
        }


ListingImageFormSet = modelformset_factory(
    ListingImage,
    form=ListingImageForm,
    extra=3,
    max_num=10,
    can_delete=True,
)
