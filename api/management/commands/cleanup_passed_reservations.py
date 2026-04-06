from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from api.models import Reservation


class Command(BaseCommand):
    help = "Auto-cancel reservations for lessons that have already passed"

    def handle(self, *args, **options):
        now = timezone.now()

        # Find reservations where lesson has passed
        passed_reservations = []

        for res in Reservation.objects.exclude(status="cancelled").filter(
            day__isnull=False, time__isnull=False
        ):
            lesson_datetime = datetime.combine(res.day, res.time)

            # Make timezone-aware if needed
            if timezone.is_naive(lesson_datetime):
                lesson_datetime = timezone.make_aware(lesson_datetime)

            if lesson_datetime < now:
                res.status = "cancelled"
                res.save()
                passed_reservations.append(res.id)

        if passed_reservations:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully auto-cancelled {len(passed_reservations)} past reservation(s): {passed_reservations}"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("No past reservations to cancel"))
