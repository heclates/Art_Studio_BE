import os
import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Reservation
from django.conf import settings

SUPABASE_URL = os.getenv('SUPABASE_URL')  # https://xyz.supabase.co
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

HEADERS = {
    'apikey': SUPABASE_SERVICE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def _to_supabase_payload(instance: Reservation):
    return {
        "id": instance.id,
        "user_id": str(instance.user.id) if instance.user else None,
        "location_id": instance.location.id if instance.location else None,
        "category_id": instance.category.id if instance.category else None,
        "direction_id": instance.direction.id if instance.direction else None,
        "visit_type": instance.visit_type,
        "art_box_type_id": instance.art_box_type.id if instance.art_box_type else None,
        "delivery_type_id": instance.delivery_type.id if instance.delivery_type else None,
        "fio": instance.fio,
        "parent_fio": instance.parent_fio,
        "child_fio": instance.child_fio,
        "child_birthdate": instance.child_birthdate.isoformat() if instance.child_birthdate else None,
        "phone": instance.phone,
        "email": instance.email,
        "parent_phone": instance.parent_phone,
        "parent_email": instance.parent_email,
        "message": instance.message,
        "day": instance.day.isoformat() if instance.day else None,
        "time": instance.time.isoformat() if instance.time else None,
        "picture_number": instance.picture_number,
        "status": instance.status,
        "created_at": instance.created_at.isoformat() if instance.created_at else None
    }

@receiver(post_save, sender=Reservation)
def sync_reservation_to_supabase(sender, instance, created, **kwargs):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    payload = _to_supabase_payload(instance)
    url = f"{SUPABASE_URL}/rest/v1/reservations"
    # upsert by id
    params = {'on_conflict': 'id'}
    try:
        resp = requests.post(url, json=[payload], headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        # логирование ошибки; не прерываем основной поток
        import logging
        logging.getLogger('api').exception("Supabase sync failed: %s", e)

@receiver(post_delete, sender=Reservation)
def delete_reservation_in_supabase(sender, instance, **kwargs):
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    url = f"{SUPABASE_URL}/rest/v1/reservations?id=eq.{instance.id}"
    try:
        resp = requests.delete(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        import logging
        logging.getLogger('api').exception("Supabase delete failed: %s", e)
