from django.core.management.base import BaseCommand
from api.models import Location, Category, Direction, ArtBoxType, DeliveryType

class Command(BaseCommand):
    def handle(self, *args, **options):
        Location.objects.get_or_create(name='Main Studio', defaults={'address': 'Prague'})
        cat_children, _ = Category.objects.get_or_create(slug='children', defaults={'title':'Дети'})
        cat_adults, _ = Category.objects.get_or_create(slug='adults', defaults={'title':'Взрослые'})
        Direction.objects.get_or_create(category=cat_children, title='Рисование')
        ArtBoxType.objects.get_or_create(slug='materials', defaults={'title':'Материалы'})
        DeliveryType.objects.get_or_create(slug='pickup', defaults={'title':'Самовывоз'})
        self.stdout.write(self.style.SUCCESS('Seed complete'))
