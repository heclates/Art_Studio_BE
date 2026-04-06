# api/management/commands/loaddirections.py
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Category, Direction

DIRECTIONS = {
    "children": [
        ("drawing", "Рисование"),
        ("ceramics", "Керамика"),
        ("creative", "Творческая мастерская"),
        ("combo", "Комбо-занятия"),
        ("prep_art_school", "Подготовка в художественную школу"),
        ("individual_child", "Индивидуальные занятия"),
        ("online_lessons", "Онлайн-уроки"),
        ("masterclasses", "Мастер-классы"),
        ("plein_air", "Пленэры"),
        ("art_camp", "Арт-лагерь"),
        ("special_events_child", "Специальные мероприятия"),
        ("art_boxes_child", "Арт-боксы"),
        ("gift_certificates_child", "Подарочные сертификаты"),
    ],
    "adults": [
        ("individual_adult", "Индивидуальные занятия"),
        ("art_parties", "Арт-вечеринки"),
        ("special_events_adult", "Специальные мероприятия"),
        ("art_boxes_adult", "Арт-боксы"),
        ("gift_certificates_adult", "Подарочные сертификаты"),
    ],
}


class Command(BaseCommand):
    help = "Load directions from i18n into DB (creates categories if missing)"

    def handle(self, *args, **options):
        with transaction.atomic():
            children_cat, _ = Category.objects.get_or_create(
                slug="children", defaults={"title": "Дети"}
            )
            adults_cat, _ = Category.objects.get_or_create(
                slug="adults", defaults={"title": "Взрослые"}
            )

            created = 0
            updated = 0
            for cat_slug, items in DIRECTIONS.items():
                cat = children_cat if cat_slug == "children" else adults_cat
                for slug, title in items:
                    obj, was_created = Direction.objects.update_or_create(
                        slug=slug, defaults={"title": title, "category": cat}
                    )
                    if was_created:
                        created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"Created Direction: {slug} -> {title}")
                        )
                    else:
                        # обновим title/category если изменились
                        changed = False
                        if obj.title != title:
                            obj.title = title
                            changed = True
                        if obj.category_id != cat.id:
                            obj.category = cat
                            changed = True
                        if changed:
                            obj.save(update_fields=["title", "category"])
                            updated += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Updated Direction: {slug} -> {title}"
                                )
                            )

            self.stdout.write(
                self.style.SUCCESS(f"Done. Created: {created}, Updated: {updated}")
            )
