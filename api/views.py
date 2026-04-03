from rest_framework import viewsets, permissions, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import get_user_model
from django.core import signing
from django.conf import settings
from django.core.mail import send_mail

from urllib.parse import unquote

from .models import Reservation, Location, Category, Direction
from .serializers import (
    ReservationSerializer,
    UserRegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()


# -------------------------
# Simple serializers
# -------------------------


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


# -------------------------
# ViewSets
# -------------------------


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

        if str(category).isdigit():
            return qs.filter(category__id=int(category))

        return qs.filter(category__slug=category)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().select_related(
        "location", "category", "direction"
    )
    serializer_class = ReservationSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """
        Filter reservations by current user for list action
        """
        if self.action == "list":
            return self.queryset.filter(user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        """
        Set the user when creating a reservation if user is authenticated
        """
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


# -------------------------
# AUTH
# -------------------------


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()

        # ❗ обязательно делаем пользователя неактивным
        user.is_active = False
        user.save(update_fields=["is_active"])

        # 🔐 генерация токена
        signer = signing.TimestampSigner(salt=settings.EMAIL_VERIFICATION_SALT)
        token = signer.sign(user.pk)

        # 🔗 ссылка для фронтенда
        verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email/?token={token}"

        # 📧 отправка email
        send_mail(
            subject="Подтверждение email",
            message=f"Перейдите по ссылке: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"detail": "verification_sent"}, status=201)


class EmailVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response({"detail": "Token missing"}, status=400)

        # очистка
        token = unquote(token).replace(" ", "").replace("\n", "")

        signer = signing.TimestampSigner(salt=settings.EMAIL_VERIFICATION_SALT)

        try:
            user_pk = signer.unsign(token, max_age=settings.EMAIL_VERIFICATION_MAX_AGE)
        except signing.SignatureExpired:
            return Response({"detail": "Token expired"}, status=400)
        except signing.BadSignature:
            return Response({"detail": "Invalid token"}, status=400)

        try:
            user = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=404)

        if user.is_active:
            return Response({"detail": "Already verified"}, status=200)

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response({"detail": "Email verified"}, status=200)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UserReservationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reservations = (
            Reservation.objects.filter(user=request.user)
            .select_related("location", "category", "direction")
            .order_by("-created_at")
        )

        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)
