"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    # Health checks (полезно для Render, Docker, Kubernetes и т.д.)
    path("healthz/", lambda request: JsonResponse({"status": "ok"})),
    path("api/health/", lambda request: JsonResponse({"status": "ok"})),
    # Admin
    path("admin/", admin.site.urls),
    # Main API
    path("api/", include("api.urls")),
    # Browsable API auth (для удобства в браузере)
    path("api-auth/", include("rest_framework.urls")),
]
