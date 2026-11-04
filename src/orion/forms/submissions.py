"""The submissions list of a form: Wagtail's, with status, search and clean exports."""

import re

import django_filters
from django.db.models import TextField
from django.db.models.functions import Cast
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.views import SubmissionsListFilterSet, SubmissionsListView

from orion.forms.models import SubmissionStatus

# What makes a spreadsheet read a cell as a formula.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")
# Phones and numbers: at most arithmetic, never functions or links.
PLAIN_NUMBER = re.compile(r"[0-9+\-(). ]*")


def neutralize_formula(value):
    """Keep a spreadsheet from running what a visitor wrote: as text, with an apostrophe
    in front, unless it is a plain number or phone."""
    if value.startswith(FORMULA_PREFIXES) and not PLAIN_NUMBER.fullmatch(value):
        return f"'{value}"
    return value


class OrionSubmissionsFilterSet(SubmissionsListFilterSet):
    q = django_filters.CharFilter(label=_("Search"), method="search")
    status = django_filters.ChoiceFilter(
        label=_("Status"), choices=SubmissionStatus.choices
    )

    def search(self, queryset, name, value):
        # The data as text: works the same in PostgreSQL and MySQL.
        return queryset.annotate(
            data_text=Cast("form_data", output_field=TextField())
        ).filter(data_text__icontains=value)


class OrionSubmissionsListView(SubmissionsListView):
    filterset_class = OrionSubmissionsFilterSet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The template links each row to Orion's submission detail.
        context["submission_detail_url_name"] = "orion_form_submission"
        return context

    def preprocess_field_value(self, field, value, export_format):
        value = super().preprocess_field_value(field, value, export_format)
        # Excel exports already write these cells as text.
        if export_format == self.FORMAT_CSV and isinstance(value, str):
            return neutralize_formula(value)
        return value

    def to_row_dict(self, item):
        """Plain values for spreadsheets: attachments as their file name."""
        row = {}
        for field in self.list_export:
            if field == "submit_time":
                value = item.submit_time
            elif field == "status":
                value = item.get_status_display()
            else:
                value = item.form_data.get(field)
                if isinstance(value, dict) and "path" in value:
                    value = value["name"]
                elif isinstance(value, list):
                    value = ", ".join(map(str, value))
            row[field] = value
        return row
