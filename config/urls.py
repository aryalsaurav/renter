"""Root URL configuration.

Template (session-auth) views live at the site root.
The JSON API (JWT-auth) is namespaced under /api/.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # ---- Browser / template (session auth) ----
    path("", include(("apps.listings.urls", "listings"), namespace="listings")),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    # ---- JSON API (JWT auth) ----
    path("api/", include("config.api_urls")),
    # ---- API schema / docs ----
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
