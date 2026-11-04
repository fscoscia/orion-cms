import csv
import datetime
import io
import re

import openpyxl
import pytest
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from orion.editor.roles import EDITORS_GROUP
from orion.forms.management.commands.orion_purge_submissions import months_ago
from orion.forms.models import (
    FormField,
    FormPage,
    FormSubmission,
    SubmissionNote,
    SubmissionStatus,
)
from orion.forms.storage import get_private_storage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def form_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ORION_FORMS_PRIVATE_ROOT = str(tmp_path / "private")
    return settings


@pytest.fixture
def jobs(home_page):
    page = FormPage(
        title="Trabajá con nosotros",
        slug="trabaja",
        form_fields=[
            FormField(label="Email", field_type="email", required=True),
            FormField(label="CV", field_type="file", required=False),
        ],
    )
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


def _submission(page, email="ana@example.com", with_cv=True, days_ago=0):
    data = {"email": email, "cv": None}
    if with_cv:
        path = get_private_storage().save(
            f"forms/{page.pk}/cv-{email}.pdf", ContentFile(b"%PDF cv")
        )
        data["cv"] = {"name": f"cv-{email}.pdf", "path": path}
    submission = FormSubmission.objects.create(page=page, form_data=data)
    if days_ago:
        FormSubmission.objects.filter(pk=submission.pk).update(
            submit_time=timezone.now() - datetime.timedelta(days=days_ago)
        )
    return submission


def _detail_url(submission):
    return reverse("orion_form_submission", args=[submission.pk])


def _list_url(page, **params):
    url = reverse("wagtailforms:list_submissions", args=[page.pk])
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return f"{url}?{query}" if query else url


class TestStatusAndNotes:
    def test_new_when_it_arrives(self, jobs):
        assert _submission(jobs).status == SubmissionStatus.NEW

    def test_read_when_opened(self, admin_client, jobs):
        submission = _submission(jobs)

        html = admin_client.get(_detail_url(submission)).content.decode()

        submission.refresh_from_db()
        assert submission.status == SubmissionStatus.READ
        assert "ana@example.com" in html
        assert reverse("orion_form_attachment", args=[submission.pk, "cv"]) in html

    def test_empty_optional_values_are_blank(self, admin_client, jobs):
        submission = _submission(jobs, with_cv=False)

        detail = admin_client.get(_detail_url(submission)).content.decode()
        listing = admin_client.get(_list_url(jobs)).content.decode()

        assert "None" not in detail.split("orion-submission__data", 1)[1]
        assert not re.search(r"<td>\s*None\s*</td>", listing)
        assert submission.get_data()["cv"] == ""

    def test_status_changes(self, admin_client, jobs):
        submission = _submission(jobs)

        admin_client.post(
            _detail_url(submission), {"action": "status", "status": "answered"}
        )

        submission.refresh_from_db()
        assert submission.status == SubmissionStatus.ANSWERED

    def test_invalid_status_is_ignored(self, admin_client, jobs):
        submission = _submission(jobs)

        admin_client.post(_detail_url(submission), {"action": "status", "status": "x"})

        submission.refresh_from_db()
        assert submission.status == SubmissionStatus.NEW

    def test_note(self, admin_client, admin_user, jobs):
        submission = _submission(jobs)

        admin_client.post(
            _detail_url(submission),
            {"action": "note", "text": "Llamé, vuelve a escribir el lunes"},
        )
        html = admin_client.get(_detail_url(submission)).content.decode()

        note = SubmissionNote.objects.get()
        assert note.author == admin_user
        assert note.created_at is not None
        assert "Llamé, vuelve a escribir el lunes" in html

    def test_empty_note_is_not_saved(self, admin_client, jobs):
        submission = _submission(jobs)

        admin_client.post(_detail_url(submission), {"action": "note", "text": "  "})

        assert not SubmissionNote.objects.exists()

    def test_editors_see_the_submissions(self, client, django_user_model, jobs):
        editor = django_user_model.objects.create_user("ana", password="x")
        editor.groups.add(Group.objects.get(name=EDITORS_GROUP))
        client.force_login(editor)

        assert client.get(_detail_url(_submission(jobs))).status_code == 200

    def test_without_permission(self, client, django_user_model, jobs):
        outsider = django_user_model.objects.create_user("beto", password="x")
        outsider.groups.add(Group.objects.create(name="Sin formularios"))
        client.force_login(outsider)
        submission = _submission(jobs)

        response = client.get(_detail_url(submission))

        assert response.status_code != 200
        submission.refresh_from_db()
        assert submission.status == SubmissionStatus.NEW


class TestList:
    def test_status_column_and_detail_link(self, admin_client, jobs):
        submission = _submission(jobs)

        html = admin_client.get(_list_url(jobs)).content.decode()

        assert "Nuevo" in html
        assert _detail_url(submission) in html

    def test_status_filter(self, admin_client, jobs):
        new = _submission(jobs, "nueva@example.com")
        answered = _submission(jobs, "vieja@example.com")
        answered.status = SubmissionStatus.ANSWERED
        answered.save()

        html = admin_client.get(_list_url(jobs, status="new")).content.decode()

        assert _detail_url(new) in html
        assert _detail_url(answered) not in html

    def test_search(self, admin_client, jobs):
        ana = _submission(jobs, "ana@example.com")
        luis = _submission(jobs, "luis@example.com")

        html = admin_client.get(_list_url(jobs, q="ana@example")).content.decode()

        assert _detail_url(ana) in html
        assert _detail_url(luis) not in html

    def test_search_with_dates(self, admin_client, jobs):
        recent = _submission(jobs, "ana@example.com")
        old = _submission(jobs, "ana.vieja@example.com", days_ago=60)
        since = (timezone.now() - datetime.timedelta(days=7)).date().isoformat()

        html = admin_client.get(
            _list_url(jobs, q="ana", date_from=since)
        ).content.decode()

        assert _detail_url(recent) in html
        assert _detail_url(old) not in html

    def test_csv_export(self, admin_client, jobs):
        _submission(jobs)

        response = admin_client.get(_list_url(jobs, export="csv"))
        content = b"".join(response.streaming_content).decode()

        assert "Nuevo" in content
        assert "cv-ana@example.com.pdf" in content
        assert "<a" not in content

    def test_xlsx_export(self, admin_client, jobs):
        _submission(jobs)

        response = admin_client.get(_list_url(jobs, export="xlsx"))
        content = (
            b"".join(response.streaming_content)
            if response.streaming
            else (response.content)
        )
        rows = list(openpyxl.load_workbook(io.BytesIO(content)).active.values)

        assert "Estado" in rows[0]
        assert "Nuevo" in rows[1]
        assert "cv-ana@example.com.pdf" in rows[1]


class TestFormulasInExports:
    @pytest.fixture
    def export_value(self, admin_client, jobs):
        def export(value, export_format):
            FormSubmission.objects.create(page=jobs, form_data={"email": value})
            response = admin_client.get(_list_url(jobs, export=export_format))
            return (
                b"".join(response.streaming_content)
                if response.streaming
                else response.content
            )

        return export

    @pytest.mark.parametrize(
        "value",
        [
            '=HYPERLINK("http://example.test","x")',
            "@SUM(A1)",
            "\t=1+1",
            "\r=1+1",
            "+cmd",
            "-cmd",
            "+\n=1",
        ],
    )
    def test_csv_neutralizes_formulas(self, export_value, value):
        content = export_value(value, "csv").decode()

        rows = list(csv.reader(io.StringIO(content, newline="")))
        assert f"'{value}" in rows[1]

    @pytest.mark.parametrize("value", ["+595 21 729 1444", "-25.5", "(021) 729-1444"])
    def test_csv_keeps_numbers_and_phones(self, export_value, value):
        content = export_value(value, "csv").decode()

        rows = list(csv.reader(io.StringIO(content)))
        assert value in rows[1]

    def test_xlsx_keeps_formulas_as_text(self, export_value):
        value = '=HYPERLINK("http://example.test","x")'
        content = export_value(value, "xlsx")

        cells = openpyxl.load_workbook(io.BytesIO(content)).active[2]
        cell = next(cell for cell in cells if cell.value == value)
        assert cell.data_type == "s"


class TestFilesAndRetention:
    def test_bulk_delete_deletes_files(
        self, admin_client, jobs, django_capture_on_commit_callbacks
    ):
        submissions = [_submission(jobs, f"{n}@example.com") for n in range(3)]
        paths = [s.form_data["cv"]["path"] for s in submissions]

        with django_capture_on_commit_callbacks(execute=True):
            admin_client.post(
                reverse("wagtailforms:delete_submissions", args=[jobs.pk])
                + "?"
                + "&".join(f"selected-submissions={s.pk}" for s in submissions)
            )

        assert not FormSubmission.objects.exists()
        assert not any(get_private_storage().exists(path) for path in paths)

    def test_deleting_the_form_deletes_files(
        self, jobs, django_capture_on_commit_callbacks
    ):
        path = _submission(jobs).form_data["cv"]["path"]

        with django_capture_on_commit_callbacks(execute=True):
            jobs.delete()

        assert not get_private_storage().exists(path)

    def test_purge(self, jobs, django_capture_on_commit_callbacks):
        old = _submission(jobs, "vieja@example.com", days_ago=400)
        recent = _submission(jobs, "reciente@example.com", days_ago=330)
        old_path = old.form_data["cv"]["path"]
        out = io.StringIO()

        with django_capture_on_commit_callbacks(execute=True):
            call_command("orion_purge_submissions", stdout=out)

        assert list(FormSubmission.objects.values_list("pk", flat=True)) == [recent.pk]
        assert not get_private_storage().exists(old_path)
        assert get_private_storage().exists(recent.form_data["cv"]["path"])
        assert "Submissions deleted: 1. Files deleted: 1." in out.getvalue()

    def test_retention_off(self, jobs, form_settings):
        form_settings.ORION_FORMS_RETENTION_MONTHS = 0
        _submission(jobs, days_ago=4000)

        call_command("orion_purge_submissions", stdout=io.StringIO())

        assert FormSubmission.objects.exists()

    @pytest.mark.parametrize(
        ("moment", "months", "expected"),
        [
            (datetime.datetime(2026, 3, 31), 1, datetime.datetime(2026, 2, 28)),
            (datetime.datetime(2026, 10, 31), 12, datetime.datetime(2025, 10, 31)),
            (datetime.datetime(2026, 1, 15), 13, datetime.datetime(2024, 12, 15)),
        ],
    )
    def test_months_ago(self, moment, months, expected):
        assert months_ago(moment, months) == expected
