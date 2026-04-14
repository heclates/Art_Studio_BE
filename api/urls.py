from django.urls import path, include
from rest_framework import routers

from .views import (
    LocationViewSet,
    CategoryViewSet,
    DirectionViewSet,
    ReservationViewSet,
    RegisterView,
    ProfileView,
    EmailVerifyView,
    UserReservationsView,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# ==================== Routers ====================
router = routers.DefaultRouter()
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"directions", DirectionViewSet, basename="direction")
router.register(r"reservations", ReservationViewSet, basename="reservation")

# ==================== URL Patterns ====================
urlpatterns = [
    # ====================== AUTH ======================
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/verify-email/", EmailVerifyView.as_view(), name="auth-email-verify"),
    path("auth/profile/", ProfileView.as_view(), name="auth-profile"),
    path(
        "auth/reservations/", UserReservationsView.as_view(), name="user-reservations"
    ),
    # ====================== JWT ======================
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # ====================== Main API ======================
    path("", include(router.urls)),
]
