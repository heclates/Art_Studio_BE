from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, F
from datetime import datetime, timedelta

from .models import (
    Profile,
    Location,
    Category,
    Direction,
    ArtBoxType,
    DeliveryType,
    Reservation,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "phone", "is_admin", "created_at")
    search_fields = ("full_name", "user__email")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "address", "active_reservations_count")
    prepopulated_fields = {"slug": ("name",)}

    def active_reservations_count(self, obj):
        count = Reservation.objects.filter(location=obj, status="confirmed").count()
        return format_html(
            '<span style="background-color: #E8F5E9; padding: 3px 8px; border-radius: 3px;">{} active</span>',
            count,
        )

    active_reservations_count.short_description = "Active Reservations"


class DirectionInline(admin.TabularInline):
    model = Direction
    extra = 1
    prepopulated_fields = {"slug": ("title",)}
    fields = ("title", "slug")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "directions_count", "total_reservations")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [DirectionInline]

    def directions_count(self, obj):
        count = obj.directions.count()
        return format_html(
            '<span style="background-color: #E3F2FD; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count,
        )

    directions_count.short_description = "Directions"

    def total_reservations(self, obj):
        count = Reservation.objects.filter(category=obj).count()
        return format_html(
            '<span style="background-color: #FFF3E0; padding: 3px 8px; border-radius: 3px;">{} total</span>',
            count,
        )

    total_reservations.short_description = "Total Reservations"


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "category", "reservations_count")
    list_filter = ("category",)
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug")

    def reservations_count(self, obj):
        count = Reservation.objects.filter(direction=obj).count()
        return format_html(
            '<span style="background-color: #F3E5F5; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count,
        )

    reservations_count.short_description = "Reservations"


@admin.register(ArtBoxType)
class ArtBoxTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(DeliveryType)
class DeliveryTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fio_display",
        "direction_title",
        "lesson_datetime_display",
        "location",
        "status_badge",
        "user_link",
        "created_at",
    )
    list_filter = ("status", "location", "category", "direction", "day", "created_at")
    search_fields = (
        "fio",
        "email",
        "phone",
        "child_fio",
        "user__email",
        "user__username",
    )
    readonly_fields = (
        "id",
        "user",
        "created_at",
        "reservation_details",
        "user_contact_info",
        "lesson_datetime_display",
    )

    fieldsets = (
        ("Reservation Info", {"fields": ("id", "user", "status", "created_at")}),
        (
            "Lesson Details",
            {
                "fields": (
                    "location",
                    "category",
                    "direction",
                    "lesson_datetime_display",
                    "visit_type",
                )
            },
        ),
        ("User Info", {"fields": ("fio", "phone", "email", "user_contact_info")}),
        (
            "Family Info (if child)",
            {
                "fields": (
                    "parent_fio",
                    "child_fio",
                    "child_birthdate",
                    "parent_phone",
                    "parent_email",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Other Details",
            {
                "fields": (
                    "art_box_type",
                    "delivery_type",
                    "picture_number",
                    "message",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def fio_display(self, obj):
        return (
            obj.fio or obj.user.get_full_name() or obj.user.username or obj.email or "—"
        )

    fio_display.short_description = "Name"

    def direction_title(self, obj):
        if obj.direction:
            return (
                f"{obj.direction.title} ({obj.category.title if obj.category else '—'})"
            )
        return obj.category.title if obj.category else "—"

    direction_title.short_description = "Class"

    def lesson_datetime_display(self, obj):
        if obj.day and obj.time:
            dt = datetime.combine(obj.day, obj.time)
            now = datetime.now()
            status = "✓ Future" if dt > now else "✗ Passed"
            return format_html(
                "<strong>{}</strong> {} <br/><small>{}</small>",
                obj.day.strftime("%d.%m.%Y"),
                obj.time.strftime("%H:%M"),
                status,
            )
        return "—"

    lesson_datetime_display.short_description = "Lesson Date & Time"

    def status_badge(self, obj):
        colors = {"pending": "#FFA500", "confirmed": "#28A745", "cancelled": "#DC3545"}
        color = colors.get(obj.status, "#6C757D")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def user_link(self, obj):
        if obj.user:
            url = reverse("admin:auth_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "—"

    user_link.short_description = "User Account"

    def reservation_details(self, obj):
        details = []
        if obj.direction:
            details.append(f"<strong>Class:</strong> {obj.direction.title}")
        if obj.location:
            details.append(f"<strong>Location:</strong> {obj.location.name}")
        if obj.visit_type:
            details.append(f"<strong>Visit Type:</strong> {obj.visit_type}")
        return format_html("<br/>".join(details)) if details else "—"

    reservation_details.short_description = "Reservation Details"

    def user_contact_info(self, obj):
        info = []
        if obj.user and obj.user.email:
            info.append(f"<strong>Email:</strong> {obj.user.email}")
        if obj.email:
            info.append(f"<strong>Email (Form):</strong> {obj.email}")
        if obj.phone:
            info.append(f"<strong>Phone:</strong> {obj.phone}")
        if obj.parent_phone:
            info.append(f"<strong>Parent Phone:</strong> {obj.parent_phone}")
        return format_html("<br/>".join(info)) if info else "—"

    user_contact_info.short_description = "Contact Info"

    actions = ["mark_confirmed", "mark_cancelled", "auto_cancel_passed"]

    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status="confirmed")
        self.message_user(request, f"{updated} reservation(s) marked as confirmed.")

    mark_confirmed.short_description = "Mark selected as Confirmed"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status="cancelled")
        self.message_user(request, f"{updated} reservation(s) marked as Cancelled.")

    mark_cancelled.short_description = "Mark selected as Cancelled"

    def auto_cancel_passed(self, request, queryset):
        """Auto-cancel reservations that have already passed"""
        now = datetime.now()
        passed = []
        for res in queryset:
            if res.day and res.time:
                dt = datetime.combine(res.day, res.time)
                if dt < now and res.status != "cancelled":
                    res.status = "cancelled"
                    res.save()
                    passed.append(str(res.id))

        if passed:
            self.message_user(
                request, f"{len(passed)} past reservation(s) auto-cancelled."
            )
        else:
            self.message_user(request, "No past reservations to cancel.")

    auto_cancel_passed.short_description = "Auto-cancel passed lessons"

    def get_queryset(self, request):
        """Show newest reservations first"""
        qs = super().get_queryset(request)
        return qs.order_by("-day", "-time", "-created_at")

    class Media:
        css = {"all": ("admin/css/admin.css",)}
