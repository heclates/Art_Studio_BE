# api/urls.py
from django.urls import path, include
from rest_framework import routers
from . import views
from .views import RegisterView, ProfileView, EmailVerifyView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = routers.DefaultRouter()
router.register(r"locations", views.LocationViewSet, basename="location")
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"directions", views.DirectionViewSet, basename="direction")
router.register(r"reservations", views.ReservationViewSet, basename="reservation")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/profile/", ProfileView.as_view(), name="auth-profile"),
    path("auth/verify-email/", EmailVerifyView.as_view(), name="auth-email-verify"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
