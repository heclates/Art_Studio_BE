from django.contrib import admin
from .models import Profile, Location, Category, Direction, ArtBoxType, DeliveryType, Reservation

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'is_admin', 'created_at')
    search_fields = ('full_name', 'user__email')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category')

@admin.register(ArtBoxType)
class ArtBoxTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')

@admin.register(DeliveryType)
class DeliveryTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'fio', 'email', 'phone', 'location', 'day', 'time', 'status', 'created_at')
    list_filter = ('status', 'location', 'created_at')
    search_fields = ('fio', 'email', 'phone', 'child_fio')
