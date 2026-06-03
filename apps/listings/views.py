"""Template (session-auth) views for listings.

Public visitors can browse/search published listings and view details (photos +
location) but cannot see owner contact info — the template guards that with
`{% if user.is_authenticated %}`. Creating/editing requires login and ownership.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.listings.forms import ListingForm, ListingImageFormSet
from apps.listings.models import Listing, ListingStatus, PropertyType
from apps.listings.tasks import notify_new_listing


def listing_list(request):
    qs = Listing.objects.published().select_related("owner").prefetch_related("images")

    city = request.GET.get("city", "").strip()
    ptype = request.GET.get("property_type", "").strip()
    q = request.GET.get("q", "").strip()
    min_rent = request.GET.get("min_rent", "").strip()
    max_rent = request.GET.get("max_rent", "").strip()

    if city:
        qs = qs.filter(city__icontains=city)
    if ptype:
        qs = qs.filter(property_type=ptype)
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(address_line__icontains=q)
        )
    if min_rent.isdigit():
        qs = qs.filter(monthly_rent__gte=min_rent)
    if max_rent.isdigit():
        qs = qs.filter(monthly_rent__lte=max_rent)

    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page,
        "property_types": PropertyType.choices,
        "filters": {
            "city": city,
            "property_type": ptype,
            "q": q,
            "min_rent": min_rent,
            "max_rent": max_rent,
        },
    }
    return render(request, "listings/listing_list.html", context)


def listing_detail(request, slug):
    listing = get_object_or_404(
        Listing.objects.select_related("owner").prefetch_related("images"), slug=slug
    )

    # Non-owners may only view published & available listings.
    is_owner = request.user.is_authenticated and listing.owner_id == request.user.id
    if not listing.is_public and not is_owner:
        raise Http404("Listing not available.")

    if not is_owner:
        Listing.objects.filter(pk=listing.pk).update(views_count=F("views_count") + 1)

    return render(
        request,
        "listings/listing_detail.html",
        {"listing": listing, "is_owner": is_owner},
    )


@login_required
def my_listings(request):
    qs = Listing.objects.for_owner(request.user).prefetch_related("images")
    return render(request, "listings/my_listings.html", {"listings": qs})


@login_required
def listing_create(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        formset = ListingImageFormSet(
            request.POST, request.FILES, queryset=Listing.images.rel.related_model.objects.none()
        )
        if form.is_valid() and formset.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.status = (
                ListingStatus.PUBLISHED
                if request.user.is_verified
                else ListingStatus.PENDING
            )
            listing.save()
            _save_images(formset, listing)
            if not request.user.is_verified:
                notify_new_listing.delay(listing.id)
                messages.info(
                    request,
                    "Your listing was submitted and is pending review.",
                )
            else:
                messages.success(request, "Your listing is now live!")
            return redirect(listing.get_absolute_url())
    else:
        form = ListingForm()
        formset = ListingImageFormSet(
            queryset=Listing.images.rel.related_model.objects.none()
        )
    return render(
        request,
        "listings/listing_form.html",
        {"form": form, "formset": formset, "mode": "create"},
    )


@login_required
def listing_update(request, slug):
    listing = get_object_or_404(Listing, slug=slug)
    if listing.owner_id != request.user.id:
        raise Http404("Listing not found.")

    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        formset = ListingImageFormSet(
            request.POST, request.FILES, queryset=listing.images.all()
        )
        if form.is_valid() and formset.is_valid():
            form.save()
            _save_images(formset, listing)
            messages.success(request, "Listing updated.")
            return redirect(listing.get_absolute_url())
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(queryset=listing.images.all())
    return render(
        request,
        "listings/listing_form.html",
        {"form": form, "formset": formset, "mode": "edit", "listing": listing},
    )


@login_required
def listing_delete(request, slug):
    listing = get_object_or_404(Listing, slug=slug)
    if listing.owner_id != request.user.id:
        raise Http404("Listing not found.")
    if request.method == "POST":
        listing.delete()
        messages.success(request, "Listing deleted.")
        return redirect("listings:my-listings")
    return render(request, "listings/listing_confirm_delete.html", {"listing": listing})


def _save_images(formset, listing):
    instances = formset.save(commit=False)
    for obj in formset.deleted_objects:
        obj.delete()
    for image in instances:
        image.listing = listing
        image.save()
