# api/views.py
from rest_framework import viewsets, permissions, serializers
from .models import Reservation, Location, Category, Direction
from .serializers import ReservationSerializer


class SimpleLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "slug", "name", "address")


class SimpleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "slug", "title")


class SimpleDirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ("id", "slug", "title", "category")


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = SimpleLocationSerializer
    permission_classes = [permissions.AllowAny]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = SimpleCategorySerializer
    permission_classes = [permissions.AllowAny]


class DirectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Direction.objects.all()
    serializer_class = SimpleDirectionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if not category:
            return qs
        try:
            if str(category).isdigit():
                return qs.filter(category__id=int(category))
            return qs.filter(category__slug=category)
        except Exception:
            return qs.none()


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().select_related(
        "location", "category", "direction"
    )
    serializer_class = ReservationSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
