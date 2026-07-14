"""Template (session-auth) views for accounts."""
import time
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.http import JsonResponse
from apps.accounts.forms import EmailAuthenticationForm, ProfileForm, SignupForm


class RenterLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class RenterLogoutView(LogoutView):
    next_page = reverse_lazy("listings:list")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("listings:my-listings")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Renter! Your account is ready.")
            return redirect("listings:my-listings")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile.html", {"form": form})


def burn_cpu(request):
    end = time.time() + 5

    while time.time() < end:
        pass

    return JsonResponse({"message": "CPU burned for 5 seconds"})