from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or str(self.user)
# api/models.py (фрагменты)
class Location(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class Direction(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='directions')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.category.title})"

class ArtBoxType(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class DeliveryType(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True)
    visit_type = models.CharField(max_length=50, blank=True, null=True)
    art_box_type = models.ForeignKey(ArtBoxType, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_type = models.ForeignKey(DeliveryType, on_delete=models.SET_NULL, null=True, blank=True)

    fio = models.CharField(max_length=255, blank=True, null=True)
    parent_fio = models.CharField(max_length=255, blank=True, null=True)
    child_fio = models.CharField(max_length=255, blank=True, null=True)
    child_birthdate = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    parent_phone = models.CharField(max_length=50, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    day = models.DateField(blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    picture_number = models.CharField(max_length=50, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reservation #{self.id} — {self.fio or self.email or 'guest'}"
