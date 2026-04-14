from rest_framework import viewsets, permissions, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import get_user_model
from django.core import signing
from django.conf import settings
from django.core.mail import send_mail
from datetime import datetime, timedelta

from urllib.parse import unquote

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils import translation

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


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = SimpleCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        """Only superusers can create/update/delete"""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all()
    serializer_class = SimpleDirectionSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        """Only superusers can create/update/delete"""
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
        """
        Filter reservations by current user for list action.
        Superusers/staff can see all reservations.
        """
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
        """
        Set the user when creating a reservation if user is authenticated
        """
        if self.request.user and self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        """
        Allow user to cancel their reservation only if it's 24+ hours away.
        Admin can cancel anytime.
        """
        reservation = self.get_object()

        # Check ownership - user must own the reservation or be admin
        if not request.user.is_superuser and reservation.user != request.user:
            return Response(
                {"detail": "You can only cancel your own reservations"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if lesson hasn't passed (non-admin users only)
        if not request.user.is_superuser:
            if reservation.day and reservation.time:
                lesson_datetime = datetime.combine(reservation.day, reservation.time)
                now = (
                    datetime.now().replace(tzinfo=lesson_datetime.tzinfo)
                    if lesson_datetime.tzinfo
                    else datetime.now()
                )

                # Can only cancel if 24+ hours away
                time_until_lesson = lesson_datetime - now
                if time_until_lesson < timedelta(hours=24):
                    return Response(
                        {"detail": "Can only cancel 24 hours before the lesson"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        # Mark as cancelled instead of deleting
        reservation.status = "cancelled"
        reservation.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


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
        user.is_active = False
        user.save(update_fields=["is_active"])

        # Генерация токена подтверждения
        signer = signing.TimestampSigner(salt=settings.EMAIL_VERIFICATION_SALT)
        token = signer.sign(user.pk)
        verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email/?token={token}"

        # Определяем язык
        user_language = request.data.get("language", "ru")  # "ru" или "cs"

        if user_language == "cs":
            translation.activate("cs")
            subject = "Potvrzení e-mailové adresy"
            template_name = "email/verify_email_cs.html"
            plain_template_name = "email/verify_email_cs.txt"  # отдельный plain-text
        else:
            translation.activate("ru")
            subject = "Подтверждение email-адреса"
            template_name = "email/verify_email_ru.html"
            plain_template_name = "email/verify_email_ru.txt"

        context = {
            "user": user,
            "verify_url": verify_url,
            "site_name": getattr(settings, "SITE_NAME", "Наш сервис"),
        }

        # Рендерим HTML и plain-text
        html_message = render_to_string(template_name, context)
        plain_message = render_to_string(plain_template_name, context)

        # Отправка письма
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,  # plain text версия
            from_email=settings.DEFAULT_FROM_EMAIL,  # рекомендую: "Название Сервиса <no-reply@tvoydomen.cz>"
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        translation.deactivate()

        return Response({"detail": "verification_sent"}, status=201)
