import calendar

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orion.forms.models import FormSubmission
from orion.forms.storage import get_private_storage

BATCH_SIZE = 500


def months_ago(moment, months):
    """The same day ``months`` months before, or the month's last day if shorter."""
    month_index = moment.year * 12 + moment.month - 1 - months
    year, month = divmod(month_index, 12)
    day = min(moment.day, calendar.monthrange(year, month + 1)[1])
    return moment.replace(year=year, month=month + 1, day=day)


class Command(BaseCommand):
    help = (
        "Delete form submissions, and their files, older than "
        "ORION_FORMS_RETENTION_MONTHS. Run it daily from cron."
    )

    def handle(self, *args, **options):
        months = settings.ORION_FORMS_RETENTION_MONTHS
        if not months:
            self.stdout.write("Retention is off (ORION_FORMS_RETENTION_MONTHS=0).")
            return
        cutoff = months_ago(timezone.now(), months)
        submissions = files = 0
        while True:
            batch = list(
                FormSubmission.objects.filter(submit_time__lt=cutoff).order_by("pk")[
                    :BATCH_SIZE
                ]
            )
            if not batch:
                break
            storage = get_private_storage()
            files += sum(
                storage.exists(value["path"])
                for submission in batch
                for _name, value in submission.attachments()
            )
            # The post_delete signal deletes the files once the deletion commits.
            with transaction.atomic():
                FormSubmission.objects.filter(pk__in=[s.pk for s in batch]).delete()
            submissions += len(batch)
        self.stdout.write(
            f"Submissions deleted: {submissions}. Files deleted: {files}. "
            f"Cutoff: {cutoff:%Y-%m-%d}."
        )
