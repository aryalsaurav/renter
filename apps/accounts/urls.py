from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.RenterLoginView.as_view(), name="login"),
    path("logout/", views.RenterLogoutView.as_view(), name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("profile/", views.profile_view, name="profile"),
    path("burn-cpu/", views.burn_cpu, name="burn-cpu"),
]
