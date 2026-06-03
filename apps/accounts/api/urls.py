from django.urls import path

from apps.accounts.api.views import MeView, RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="api-register"),
    path("auth/me/", MeView.as_view(), name="api-me"),
]
