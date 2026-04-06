# api/serializers.py
import logging
from rest_framework import serializers
from django.db import transaction
from .models import Profile, Reservation, Location, Category, Direction
from .choices import (
    DIRECTION_TITLE_TO_SLUG,
    LOCATION_TITLE_TO_SLUG,
    CATEGORY_TITLE_TO_SLUG,
)
from django.contrib.auth import get_user_model
from django.core import signing
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _model_has_field(model, field_name):
    """
    Возвращает True если модель model имеет поле field_name, иначе False.
    Используется чтобы не делать filter по несуществующему полю (избежать FieldError).
    """
    try:
        model._meta.get_field(field_name)
        return True
    except Exception:
        return False


class ReservationSerializer(serializers.ModelSerializer):
    location_id = serializers.IntegerField(required=False, allow_null=True)
    location_title = serializers.CharField(required=False, allow_null=True)
    location_slug = serializers.CharField(required=False, allow_null=True)

    category_id = serializers.IntegerField(required=False, allow_null=True)
    category_title = serializers.CharField(required=False, allow_null=True)
    category_slug = serializers.CharField(required=False, allow_null=True)

    direction_id = serializers.IntegerField(required=False, allow_null=True)
    direction_title = serializers.CharField(required=False, allow_null=True)
    direction_slug = serializers.CharField(required=False, allow_null=True)

    user_username = serializers.CharField(read_only=True)
    user_email = serializers.CharField(read_only=True)
    user_display_name = serializers.CharField(read_only=True)
    user_first_name = serializers.CharField(read_only=True)
    user_last_name = serializers.CharField(read_only=True)
    user_phone = serializers.CharField(read_only=True)

    class Meta:
        model = Reservation
        fields = "__all__"

    def _resolve_fk(
        self, model, id_val=None, slug_val=None, title_val=None, title_map=None
    ):
        """
        Безопасное разрешение FK:
        1) по id
        2) по slug (если модель имеет поле slug)
        3) по title -> slug через title_map (если есть)
        4) по реальным текстовым полям модели (title/name), только если поле существует
        Возвращает объект модели или None.
        """
        # 1) by id
        if id_val:
            try:
                obj = model.objects.filter(pk=id_val).first()
                if obj:
                    return obj
            except Exception as e:
                logger.debug("Resolve by id failed for %s id=%s: %s", model, id_val, e)

        # 2) by slug
        if slug_val and _model_has_field(model, "slug"):
            try:
                obj = model.objects.filter(slug=slug_val).first()
                if obj:
                    return obj
            except Exception as e:
                logger.debug(
                    "Resolve by slug failed for %s slug=%s: %s", model, slug_val, e
                )

        # 3) title -> slug mapping
        if title_val:
            if title_map and title_val in title_map and _model_has_field(model, "slug"):
                try:
                    slug = title_map[title_val]
                    obj = model.objects.filter(slug=slug).first()
                    if obj:
                        return obj
                except Exception as e:
                    logger.debug(
                        "Resolve by title->slug mapping failed for %s title=%s: %s",
                        model,
                        title_val,
                        e,
                    )

            # 4) search by available textual fields (only if field exists)
            for field in ("title", "name"):
                if _model_has_field(model, field):
                    try:
                        kwargs = {f"{field}__iexact": title_val}
                        obj = model.objects.filter(**kwargs).first()
                        if obj:
                            return obj
                    except Exception as e:
                        logger.debug(
                            "Resolve by field %s failed for %s value=%s: %s",
                            field,
                            model,
                            title_val,
                            e,
                        )

        return None

    def validate(self, attrs):
        """
        Разрешаем direction/category/location через id/slug/title.
        Если фронт отправил любое из полей (id/slug/title) и объект не найден — возвращаем ValidationError.
        Также нормализуем время формата HH:MM -> HH:MM:SS.
        """
        # debug: логируем ключи входящих данных (можно убрать после отладки)
        logger.debug(
            "ReservationSerializer.validate payload keys: %s", list(attrs.keys())
        )

        dir_obj = self._resolve_fk(
            Direction,
            id_val=attrs.get("direction_id"),
            slug_val=attrs.get("direction_slug"),
            title_val=attrs.get("direction_title"),
            title_map=DIRECTION_TITLE_TO_SLUG,
        )
        if (
            any(
                k in attrs
                for k in ("direction_id", "direction_slug", "direction_title")
            )
            and not dir_obj
        ):
            raise serializers.ValidationError(
                {"direction": "Unknown direction. Update mapping or DB."}
            )
        attrs["direction_obj"] = dir_obj

        cat_obj = self._resolve_fk(
            Category,
            id_val=attrs.get("category_id"),
            slug_val=attrs.get("category_slug"),
            title_val=attrs.get("category_title"),
            title_map=CATEGORY_TITLE_TO_SLUG,
        )
        if (
            any(k in attrs for k in ("category_id", "category_slug", "category_title"))
            and not cat_obj
        ):
            raise serializers.ValidationError({"category": "Unknown category."})
        attrs["category_obj"] = cat_obj

        loc_obj = self._resolve_fk(
            Location,
            id_val=attrs.get("location_id"),
            slug_val=attrs.get("location_slug"),
            title_val=attrs.get("location_title"),
            title_map=LOCATION_TITLE_TO_SLUG,
        )
        if (
            any(k in attrs for k in ("location_id", "location_slug", "location_title"))
            and not loc_obj
        ):
            raise serializers.ValidationError({"location": "Unknown location."})
        attrs["location_obj"] = loc_obj

        # prevent duplicate bookings for same user/place/day/time
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and loc_obj and attrs.get("day"):
            qs = Reservation.objects.filter(
                user=user,
                location=loc_obj,
                day=attrs["day"],
            ).exclude(status="cancelled")

            if attrs.get("time") is None:
                qs = qs.filter(time__isnull=True)
            else:
                qs = qs.filter(time=attrs["time"])

            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["duplicate_booking"]}
                )

        # normalize time string "HH:MM" -> "HH:MM:SS"
        time_val = attrs.get("time")
        if time_val and isinstance(time_val, str) and len(time_val.split(":")) == 2:
            attrs["time"] = f"{time_val}:00"

        return attrs

    def create(self, validated_data):
        direction_obj = validated_data.pop("direction_obj", None)
        category_obj = validated_data.pop("category_obj", None)
        location_obj = validated_data.pop("location_obj", None)

        # remove helper fields that are not model fields
        for k in (
            "direction_id",
            "direction_title",
            "direction_slug",
            "category_id",
            "category_title",
            "category_slug",
            "location_id",
            "location_title",
            "location_slug",
            "direction",
            "category",
            "location",
        ):
            validated_data.pop(k, None)

        with transaction.atomic():
            reservation = Reservation.objects.create(
                direction=direction_obj,
                category=category_obj,
                location=location_obj,
                **validated_data,
            )
        return reservation

    def to_representation(self, instance):
        """
        Customize the representation to include title and slug from related objects, а также user_first_name, user_last_name, user_phone
        """
        data = super().to_representation(instance)

        # Fill location fields
        if instance.location:
            data["location_title"] = instance.location.name
            data["location_slug"] = instance.location.slug
        else:
            data["location_title"] = None
            data["location_slug"] = None

        # Fill category fields
        if instance.category:
            data["category_title"] = instance.category.title
            data["category_slug"] = instance.category.slug
        else:
            data["category_title"] = None
            data["category_slug"] = None

        # Fill direction fields
        if instance.direction:
            data["direction_title"] = instance.direction.title
            data["direction_slug"] = instance.direction.slug
        else:
            data["direction_title"] = None
            data["direction_slug"] = None

        # User info for superuser context menu
        if instance.user:
            data["user_username"] = instance.user.username
            data["user_email"] = instance.user.email
            data["user_first_name"] = getattr(instance.user, "first_name", None)
            data["user_last_name"] = getattr(instance.user, "last_name", None)
            # phone from profile if exists
            profile = getattr(instance.user, "profile", None)
            data["user_phone"] = getattr(profile, "phone", None) if profile else None
            full_name = instance.user.get_full_name().strip()
            data["user_display_name"] = full_name or instance.user.username
        else:
            data["user_username"] = None
            data["user_email"] = None
            data["user_first_name"] = None
            data["user_last_name"] = None
            data["user_phone"] = None
            data["user_display_name"] = None

        return data


User = get_user_model()


class ProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("full_name", "phone", "is_admin")


class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileNestedSerializer(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "profile",
        )


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()

        self.send_verification_email(user)
        return user

    def send_verification_email(self, user):
        signer = signing.TimestampSigner(salt=settings.EMAIL_VERIFICATION_SALT)
        token = signer.sign(user.pk)

        verify_url = f"{settings.FRONTEND_BASE_URL}/verify-email/?token={token}"

        subject = "Подтверждение email"
        text = f"Перейдите по ссылке: {verify_url}"
        html = f"<p>Подтвердите email: <a href='{verify_url}'>Нажмите здесь</a></p>"

        msg = EmailMultiAlternatives(
            subject, text, settings.DEFAULT_FROM_EMAIL, [user.email]
        )
        msg.attach_alternative(html, "text/html")
        msg.send()
