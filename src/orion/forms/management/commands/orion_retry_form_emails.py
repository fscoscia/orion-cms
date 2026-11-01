import datetime

from django.conf import settings
from django.core.mail import get_connection
from django.core.management.base import BaseCommand
from django.utils import timezone

from orion.forms.models import EmailNotice, FormPage, FormSubmission


class Command(BaseCommand):
    help = (
        "Send again the email notices of form submissions that could not go out, "
        "from the last ORION_FORMS_EMAIL_RETRY_DAYS days. Run it from cron, for "
        "example every 15 minutes."
    )

    def handle(self, *args, **options):
        since = timezone.now() - datetime.timedelta(
            days=settings.ORION_FORMS_EMAIL_RETRY_DAYS
        )
        pending = list(
            FormSubmission.objects.filter(
                email_notice=EmailNotice.PENDING, submit_time__gte=since
            ).order_by("submit_time")
        )
        if not pending:
            self.stdout.write("No pending email notices.")
            return
        pages = {
            page.pk: page
            for page in FormPage.objects.filter(
                pk__in={submission.page_id for submission in pending}
            )
        }
        connection = get_connection()
        try:
            connection.open()
        except Exception as error:  # noqa: BLE001 - reported, retried next run
            self.stderr.write(f"The mail server failed: {error}")
            return
        sent = 0
        try:
            for submission in pending:
                page = pages.get(submission.page_id)
                if page is None or not page.get_recipients():
                    continue
                if not page.send_notice(submission, connection=connection):
                    # The server stopped answering: the rest wait for the next run.
                    self.stderr.write("The mail server failed; stopping.")
                    break
                sent += 1
        finally:
            connection.close()
        self.stdout.write(
            f"Email notices sent: {sent}. Pending: {len(pending) - sent}."
        )
