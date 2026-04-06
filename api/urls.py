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

router = routers.DefaultRouter()
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"directions", DirectionViewSet, basename="direction")
router.register(r"reservations", ReservationViewSet, basename="reservation")

urlpatterns = [
    # AUTH
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/profile/", ProfileView.as_view(), name="auth-profile"),
    path(
        "auth/reservations/", UserReservationsView.as_view(), name="user-reservations"
    ),
    path("auth/verify-email/", EmailVerifyView.as_view(), name="auth-email-verify"),
    # JWT
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API
    path("", include(router.urls)),
]
