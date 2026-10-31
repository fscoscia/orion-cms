"""Scheduled publishing: the calendar's entries and the check that the periodic
``publish_scheduled`` task is running."""

import calendar
import datetime
from dataclasses import dataclass

from django.apps import apps
from django.db.models import CharField
from django.db.models.functions import Cast
from django.utils import formats, timezone
from wagtail.models import DraftStateMixin, Page, Revision
from wagtail.permission_policies.pages import PagePermissionPolicy

# The task runs every few minutes; past this delay, it is not running.
OVERDUE_AFTER = datetime.timedelta(hours=1)

PUBLISH = "publish"
EXPIRE = "expire"


@dataclass
class Entry:
    kind: str
    page: Page
    at: datetime.datetime
    is_overdue: bool


def _scheduled_models():
    """The models that ``publish_scheduled`` publishes and expires."""
    return [Page] + [
        model
        for model in apps.get_models()
        if issubclass(model, DraftStateMixin) and not issubclass(model, Page)
    ]


def overdue_count(now=None):
    """Publications and expiries due for longer than OVERDUE_AFTER and not applied."""
    cutoff = (now or timezone.now()) - OVERDUE_AFTER
    count = Revision.objects.filter(approved_go_live_at__lt=cutoff).count()
    for model in _scheduled_models():
        count += model.objects.filter(live=True, expire_at__lt=cutoff).count()
    return count


def month_bounds(year, month):
    start = timezone.make_aware(datetime.datetime(year, month, 1))
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    return start, timezone.make_aware(datetime.datetime(next_year, next_month, 1))


def month_entries(user, year, month, now=None):
    """Scheduled publications and expiries of the month, of pages the user can edit,
    by local date."""
    now = now or timezone.now()
    start, end = month_bounds(year, month)
    pages = PagePermissionPolicy().instances_user_has_permission_for(user, "change")
    overdue_before = now - OVERDUE_AFTER
    revisions = Revision.page_revisions.filter(
        approved_go_live_at__gte=start,
        approved_go_live_at__lt=end,
        object_id__in=pages.annotate(
            pk_text=Cast("pk", output_field=CharField())
        ).values("pk_text"),
    )
    # The revision is the version that goes live, with its own title.
    entries = [
        Entry(
            PUBLISH,
            revision.as_object(),
            revision.approved_go_live_at,
            revision.approved_go_live_at < overdue_before,
        )
        for revision in revisions
    ]
    entries += [
        Entry(EXPIRE, page, page.expire_at, page.expire_at < overdue_before)
        for page in pages.filter(live=True, expire_at__gte=start, expire_at__lt=end)
    ]
    by_day = {}
    for entry in sorted(entries, key=lambda entry: entry.at):
        by_day.setdefault(timezone.localtime(entry.at).date(), []).append(entry)
    return by_day


def month_weeks(year, month):
    """The month's weeks as lists of dates (None outside the month), starting on the
    active language's first day of the week."""
    # FIRST_DAY_OF_WEEK: 0 is Sunday; calendar's firstweekday: 0 is Monday.
    first_day = (int(formats.get_format("FIRST_DAY_OF_WEEK")) - 1) % 7
    return [
        [datetime.date(year, month, day) if day else None for day in week]
        for week in calendar.Calendar(first_day).monthdayscalendar(year, month)
    ]
