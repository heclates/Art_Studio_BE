from rest_framework import viewsets, permissions, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import get_user_model
from django.core import signing
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

from datetime import datetime, timedelta
from urllib.parse import unquote

from .models import Reservation, Location, Category, Direction
from .serializers import (
    ReservationSerializer,
    UserRegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()

# =========================
# Simple Serializers
# =========================


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


# =========================
# ViewSets
# =========================


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = SimpleLocationSerializer
    permission_classes = [permissions.AllowAny]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = SimpleCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all()
    serializer_class = SimpleDirectionSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

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
        if self.action == "list":
            if (
                self.request.user.is_authenticated
                and self.request.user.is_superuser
                and self.request.user.is_staff
            ):
                return self.queryset
            return self.queryset.filter(user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()

        if not request.user.is_superuser and reservation.user != request.user:
            return Response(
                {"detail": "You can only cancel your own reservations"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not request.user.is_superuser:
            if reservation.day and reservation.time:
                lesson_datetime = datetime.combine(reservation.day, reservation.time)
                now = (
                    datetime.now().replace(tzinfo=lesson_datetime.tzinfo)
                    if lesson_datetime.tzinfo
                    else datetime.now()
                )

                if lesson_datetime - now < timedelta(hours=24):
                    return Response(
                        {"detail": "Can only cancel 24 hours before the lesson"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        reservation.status = "cancelled"
        reservation.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
# AUTH Views
# =========================


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        user = serializer.save()
        user.is_active = False
        user.save(update_fields=["is_active"])

        # Генерация токена
        signer = signing.TimestampSigner(salt=settings.EMAIL_VERIFICATION_SALT)
        token = signer.sign(user.pk)
        verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email/?token={token}"

        # Определяем язык пользователя
        user_language = request.data.get("language", "ru")

        if user_language == "en":
            translation.activate("en")
            subject = "Potvrzení e-mailové adresy"
            html_template = "email/verify_email_cs.html"
            txt_template = "email/verify_email_cs.txt"
        else:
            translation.activate("ru")
            subject = "Подтверждение email-адреса"
            html_template = "email/verify_email_ru.html"
            txt_template = "email/verify_email_ru.txt"

        context = {
            "user": user,
            "verify_url": verify_url,
            "site_name": getattr(settings, "SITE_NAME", "Наш сервис"),
        }

        html_message = render_to_string(html_template, context)
        plain_message = render_to_string(txt_template, context)

        # Отправка письма
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        translation.deactivate()

        return Response({"detail": "verification_sent"}, status=201)


class EmailVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token missing"}, status=400)

        token = unquote(token).strip()

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
    """Профиль пользователя"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UserReservationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_superuser and request.user.is_staff:
            reservations = Reservation.objects.all()
        else:
            reservations = Reservation.objects.filter(user=request.user)

        reservations = reservations.select_related(
            "location", "category", "direction"
        ).order_by("-created_at")

        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)
