# api/serializers.py
from rest_framework import serializers
from django.db import transaction
from .models import Reservation, Location, Category, Direction, ArtBoxType, DeliveryType
from .choices import DIRECTION_TITLE_TO_SLUG, LOCATION_TITLE_TO_SLUG, CATEGORY_TITLE_TO_SLUG

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

    class Meta:
        model = Reservation
        fields = '__all__'

    def _resolve_fk_strict(self, model, id_val=None, slug_val=None, title_val=None, title_to_slug_map=None):
        if id_val:
            obj = model.objects.filter(pk=id_val).first()
            if obj:
                return obj
        if slug_val and hasattr(model, 'slug'):
            obj = model.objects.filter(slug=slug_val).first()
            if obj:
                return obj
        if title_val:
            if title_to_slug_map and title_val in title_to_slug_map:
                slug = title_to_slug_map[title_val]
                if hasattr(model, 'slug'):
                    obj = model.objects.filter(slug=slug).first()
                    if obj:
                        return obj
            for field in ('title', 'name'):
                kwargs = {f'{field}__iexact': title_val}
                obj = model.objects.filter(**kwargs).first()
                if obj:
                    return obj
        return None

    def validate(self, attrs):
        dir_obj = self._resolve_fk_strict(Direction,
                                          id_val=attrs.get('direction_id'),
                                          slug_val=attrs.get('direction_slug'),
                                          title_val=attrs.get('direction_title'),
                                          title_to_slug_map=DIRECTION_TITLE_TO_SLUG)
        if any(k in attrs for k in ('direction_id','direction_slug','direction_title')) and not dir_obj:
            raise serializers.ValidationError({'direction': 'Unknown direction. Update mapping or DB.'})
        attrs['direction_obj'] = dir_obj

        cat_obj = self._resolve_fk_strict(Category,
                                          id_val=attrs.get('category_id'),
                                          slug_val=attrs.get('category_slug'),
                                          title_val=attrs.get('category_title'),
                                          title_to_slug_map=CATEGORY_TITLE_TO_SLUG)
        if any(k in attrs for k in ('category_id','category_slug','category_title')) and not cat_obj:
            raise serializers.ValidationError({'category': 'Unknown category.'})
        attrs['category_obj'] = cat_obj

        loc_obj = self._resolve_fk_strict(Location,
                                          id_val=attrs.get('location_id'),
                                          slug_val=attrs.get('location_slug'),
                                          title_val=attrs.get('location_title'),
                                          title_to_slug_map=LOCATION_TITLE_TO_SLUG)
        if any(k in attrs for k in ('location_id','location_slug','location_title')) and not loc_obj:
            raise serializers.ValidationError({'location': 'Unknown location.'})
        attrs['location_obj'] = loc_obj

        return attrs

    def create(self, validated_data):
        direction_obj = validated_data.pop('direction_obj', None)
        category_obj = validated_data.pop('category_obj', None)
        location_obj = validated_data.pop('location_obj', None)

        for k in ('direction_id','direction_title','direction_slug','category_id','category_title','category_slug','location_id','location_title','location_slug'):
            validated_data.pop(k, None)

        with transaction.atomic():
            reservation = Reservation.objects.create(
                direction=direction_obj,
                category=category_obj,
                location=location_obj,
                **validated_data
            )
        return reservation
