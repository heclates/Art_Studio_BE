# api/management/commands/seed_slugs.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction, IntegrityError
from api.models import Direction, Location, Category


def make_unique_slug(model, base_slug, instance_id=None):
    if not base_slug:
        base_slug = f'item-{instance_id or "x"}'
    slug = base_slug
    counter = 1
    while model.objects.filter(slug=slug).exclude(pk=instance_id).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


class Command(BaseCommand):
    help = "Fill slug fields for Direction/Location/Category safely"

    def handle(self, *args, **options):
        for d in Direction.objects.all():
            if d.slug:
                continue
            candidate = slugify(d.title or "", allow_unicode=True).strip()
            candidate = candidate or slugify(d.title or "", allow_unicode=False).strip()
            candidate = candidate or f"direction-{d.pk}"
            unique = make_unique_slug(Direction, candidate, instance_id=d.pk)
            d.slug = unique
            try:
                with transaction.atomic():
                    d.save(update_fields=["slug"])
                self.stdout.write(
                    self.style.SUCCESS(f"Updated Direction: {d.title} -> {d.slug}")
                )
            except IntegrityError as e:
                self.stderr.write(f"IntegrityError for Direction id={d.pk}: {e}")
                alt = make_unique_slug(
                    Direction, f"{candidate}-{d.pk}", instance_id=d.pk
                )
                d.slug = alt
                d.save(update_fields=["slug"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated Direction (retry): {d.title} -> {d.slug}"
                    )
                )

        for l in Location.objects.all():
            if l.slug:
                continue
            candidate = slugify(l.name or "", allow_unicode=True).strip()
            candidate = candidate or slugify(l.name or "", allow_unicode=False).strip()
            candidate = candidate or f"location-{l.pk}"
            unique = make_unique_slug(Location, candidate, instance_id=l.pk)
            l.slug = unique
            try:
                with transaction.atomic():
                    l.save(update_fields=["slug"])
                self.stdout.write(
                    self.style.SUCCESS(f"Updated Location: {l.name} -> {l.slug}")
                )
            except IntegrityError as e:
                self.stderr.write(f"IntegrityError for Location id={l.pk}: {e}")
                alt = make_unique_slug(
                    Location, f"{candidate}-{l.pk}", instance_id=l.pk
                )
                l.slug = alt
                l.save(update_fields=["slug"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated Location (retry): {l.name} -> {l.slug}"
                    )
                )

        for c in Category.objects.all():
            if c.slug:
                continue
            candidate = slugify(c.title or "", allow_unicode=True).strip()
            candidate = candidate or slugify(c.title or "", allow_unicode=False).strip()
            candidate = candidate or f"category-{c.pk}"
            unique = make_unique_slug(Category, candidate, instance_id=c.pk)
            c.slug = unique
            try:
                with transaction.atomic():
                    c.save(update_fields=["slug"])
                self.stdout.write(
                    self.style.SUCCESS(f"Updated Category: {c.title} -> {c.slug}")
                )
            except IntegrityError as e:
                self.stderr.write(f"IntegrityError for Category id={c.pk}: {e}")
                alt = make_unique_slug(
                    Category, f"{candidate}-{c.pk}", instance_id=c.pk
                )
                c.slug = alt
                c.save(update_fields=["slug"])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated Category (retry): {c.title} -> {c.slug}"
                    )
                )
