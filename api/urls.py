from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'locations', views.LocationViewSet, basename='location')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'directions', views.DirectionViewSet, basename='direction')
router.register(r'reservations', views.ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]
