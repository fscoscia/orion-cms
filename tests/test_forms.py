import io
import re

import pytest
from django.contrib.auth.models import Group
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from wagtail.models import Page

from orion.core.blocks import ContentStreamBlock
from orion.editor.roles import ADMINISTRATORS_GROUP
from orion.forms.checks import check_private_root
from orion.forms.models import FormField, FormPage, FormSubmission
from orion.forms.storage import get_private_root, get_private_storage
from orion.pages.models import ContentPage
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def form_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ORION_FORMS_PRIVATE_ROOT = str(tmp_path / "private")
    settings.ORION_FORMS_MIN_SECONDS = 0
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    return settings


def _form_page(parent, title="Contacto", slug="contacto", fields=None, **page_fields):
    fields = fields or [
        ("Nombre", "singleline", True),
        ("Email", "email", True),
        ("Teléfono", "phone", False),
        ("Mensaje", "multiline", True),
    ]
    page = FormPage(
        title=title,
        slug=slug,
        to_address="equipo@example.com",
        subject="Consulta",
        form_fields=[
            FormField(label=label, field_type=field_type, required=required)
            for label, field_type, required in fields
        ],
        **page_fields,
    )
    parent.add_child(instance=page)
    page.save_revision().publish()
    return page


@pytest.fixture
def contact(home_page):
    return _form_page(home_page)


def _token(client, url):
    html = client.get(url).content.decode()
    return re.search(r'name="rendered_at" value="([^"]+)"', html).group(1)


def _send(client, page, data=None, url=None, **extra):
    url = url or page.url
    payload = {
        "nombre": "Ana",
        "email": "ana@example.com",
        "mensaje": "Hola",
        "consent": "on",
        "rendered_at": _token(client, url),
        **(data or {}),
    }
    return client.post(page.url, payload, **extra)


class TestFormPage:
    def test_shows_the_fields(self, client, contact):
        html = client.get(contact.url).content.decode()

        for name in ("nombre", "email", "telefono", "mensaje", "consent"):
            assert f'name="{name}"' in html
        assert re.search(r'<input type="tel"[^>]*name="telefono"', html)
        assert 'enctype="multipart/form-data"' in html

    def test_valid_submission(self, client, contact):
        response = _send(client, contact, {"telefono": "+595 21 000-000"})

        submission = FormSubmission.objects.get()
        assert response.status_code == 200
        assert "Gracias" in response.content.decode()
        assert submission.form_data["nombre"] == "Ana"
        assert submission.form_data["telefono"] == "+595 21 000-000"
        assert "consent" not in submission.form_data
        assert "website" not in submission.form_data

    def test_server_validation(self, client, contact):
        response = _send(client, contact, {"email": "no-es-email", "telefono": "abc"})

        html = response.content.decode()
        assert not FormSubmission.objects.exists()
        assert 'aria-invalid="true"' in html
        assert "orion-form__error" in html

    def test_thank_you_text(self, client, home_page):
        page = _form_page(home_page, thank_you_text="<p>¡Gracias, Ana!</p>")

        assert "¡Gracias, Ana!" in _send(client, page).content.decode()

    def test_thank_you_page(self, client, home_page):
        thanks = ContentPage(title="Gracias", slug="gracias")
        home_page.add_child(instance=thanks)
        thanks.save_revision().publish()
        page = _form_page(home_page, thank_you_page=thanks)

        response = _send(client, page)

        assert response.status_code == 303
        assert response["Location"] == "/gracias/"


class TestAttachments:
    @pytest.fixture
    def jobs(self, home_page):
        return _form_page(
            home_page,
            "Trabajá con nosotros",
            "trabaja",
            fields=[("Nombre", "singleline", True), ("CV", "file", True)],
        )

    def _send_cv(self, client, jobs, name="cv.pdf", content=b"%PDF-1.4 cv"):
        return client.post(
            jobs.url,
            {
                "nombre": "Ana",
                "cv": SimpleUploadedFile(name, content),
                "consent": "on",
                "rendered_at": _token(client, jobs.url),
            },
        )

    def test_saved_outside_media(self, client, jobs, form_settings):
        self._send_cv(client, jobs)

        data = FormSubmission.objects.get().form_data["cv"]
        assert data["name"] == "cv.pdf"
        assert get_private_storage().exists(data["path"])
        assert form_settings.MEDIA_ROOT not in get_private_root().parents
        assert not list(form_settings.MEDIA_ROOT.glob("**/cv*.pdf"))

    @pytest.mark.parametrize(
        ("name", "content"),
        [("virus.exe", b"MZ"), ("enorme.pdf", b"%PDF" + b"0" * (5 * 1024 * 1024 + 1))],
    )
    def test_rejected(self, client, jobs, name, content):
        response = self._send_cv(client, jobs, name, content)

        assert response.status_code == 200
        assert not FormSubmission.objects.exists()
        assert "orion-form__error" in response.content.decode()

    def test_download_with_permission(self, client, jobs, django_user_model):
        self._send_cv(client, jobs)
        submission = FormSubmission.objects.get()
        url = reverse("orion_form_attachment", args=[submission.pk, "cv"])
        administrator = django_user_model.objects.create_user("jefa", password="x")
        administrator.groups.add(Group.objects.get(name=ADMINISTRATORS_GROUP))
        client.force_login(administrator)

        response = client.get(url)

        assert response.status_code == 200
        assert b"".join(response.streaming_content) == b"%PDF-1.4 cv"
        assert "attachment" in response["Content-Disposition"]
        assert url in submission.get_data()["cv"]

    def test_no_download_without_permission(self, client, jobs, django_user_model):
        self._send_cv(client, jobs)
        submission = FormSubmission.objects.get()
        url = reverse("orion_form_attachment", args=[submission.pk, "cv"])
        outsider = django_user_model.objects.create_user("beto", password="x")
        outsider.groups.add(Group.objects.create(name="Sin formularios"))

        anonymous = Client().get(url)
        client.force_login(outsider)
        signed_in = client.get(url)

        assert anonymous.status_code == 302
        assert signed_in.status_code != 200

    def test_private_root_inside_media_is_an_error(self, form_settings):
        form_settings.ORION_FORMS_PRIVATE_ROOT = str(form_settings.MEDIA_ROOT / "x")

        assert [error.id for error in check_private_root(None)] == ["orion.E005"]


class TestSpamProtection:
    def test_trap_filled(self, client, contact):
        response = _send(client, contact, {"website": "http://spam.example"})

        assert not FormSubmission.objects.exists()
        assert not mail.outbox
        assert "orion-form__alert" in response.content.decode()

    def test_too_fast(self, client, contact, form_settings):
        form_settings.ORION_FORMS_MIN_SECONDS = 30

        _send(client, contact)

        assert not FormSubmission.objects.exists()

    def test_token_from_another_form(self, client, contact, home_page):
        other = _form_page(home_page, "Otro", "otro")

        _send(client, contact, {"rendered_at": _token(client, other.url)})

        assert not FormSubmission.objects.exists()

    def test_rate_limit(self, client, contact):
        for _number in range(5):
            _send(client, contact)

        response = _send(client, contact)

        assert FormSubmission.objects.count() == 5
        assert "orion-form__alert" in response.content.decode()

    def test_csrf_is_required(self, contact):
        client = Client(enforce_csrf_checks=True)

        response = _send(client, contact)

        assert response.status_code == 403
        assert not FormSubmission.objects.exists()


class TestConsent:
    def test_required(self, client, contact):
        _send(client, contact, {"consent": ""})

        assert not FormSubmission.objects.exists()

    def test_recorded(self, client, contact):
        _send(client, contact)

        assert FormSubmission.objects.get().consent_at is not None

    def test_links_the_privacy_page(self, client, contact, home_page):
        privacy = ContentPage(title="Privacidad", slug="privacidad")
        home_page.add_child(instance=privacy)
        privacy.save_revision().publish()
        site_settings = SiteSettings.load()
        site_settings.privacy_page = privacy
        site_settings.save()

        html = client.get(contact.url).content.decode()

        assert re.search(
            r'<a href="/privacidad/"[^>]*>política de privacidad</a>', html
        )


class TestEditorLimits:
    def _admin_form(self, page, field_count, field_type="singleline"):
        form_class = page.get_edit_handler().get_form_class()
        data = {
            "title": page.title,
            "slug": page.slug,
            "form_fields-TOTAL_FORMS": str(field_count),
            "form_fields-INITIAL_FORMS": "0",
            "form_fields-MIN_NUM_FORMS": "0",
            "form_fields-MAX_NUM_FORMS": "1000",
        }
        for number in range(field_count):
            data.update(
                {
                    f"form_fields-{number}-label": f"Campo {number}",
                    f"form_fields-{number}-field_type": field_type,
                    f"form_fields-{number}-ORDER": str(number),
                }
            )
        return form_class(data, instance=page, parent_page=page.get_parent())

    def test_too_many_fields(self, contact):
        form = self._admin_form(contact, 31)

        assert not form.is_valid()
        assert "30" in str(form.non_field_errors())

    def test_field_type_not_allowed(self, contact, form_settings):
        form_settings.ORION_FORMS_FIELD_TYPES = ["singleline", "email"]

        assert not self._admin_form(contact, 1, "file").is_valid()
        assert self._admin_form(contact, 1, "email").is_valid()


class TestEmail:
    def test_notice(self, client, home_page):
        page = _form_page(home_page, from_name="Clínica Ejemplo")

        _send(client, page)

        message = mail.outbox[0]
        assert message.to == ["equipo@example.com"]
        assert message.reply_to == ["ana@example.com"]
        assert message.from_email.startswith('"Clínica Ejemplo" <')
        assert "Mensaje: Hola" in message.body

    def test_attachment_as_a_link(self, client, home_page):
        page = _form_page(
            home_page, fields=[("Email", "email", True), ("CV", "file", False)]
        )
        client.post(
            page.url,
            {
                "email": "ana@example.com",
                "cv": SimpleUploadedFile("cv.pdf", b"%PDF"),
                "consent": "on",
                "rendered_at": _token(client, page.url),
            },
        )

        message = mail.outbox[0]
        assert not message.attachments
        assert "cv.pdf" in message.body
        assert reverse("wagtailforms:list_submissions", args=[page.pk]) in message.body

    def test_mail_error_keeps_the_submission(self, client, contact, form_settings):
        form_settings.EMAIL_BACKEND = "tests.test_forms.FailingBackend"

        response = _send(client, contact)

        assert FormSubmission.objects.exists()
        assert "Gracias" in response.content.decode()

    def test_test_email_from_the_admin(self, admin_client, contact):
        url = reverse("orion_form_test_email", args=[contact.pk])
        edit_html = admin_client.get(
            reverse("wagtailadmin_pages:edit", args=[contact.pk])
        ).content.decode()

        admin_client.post(url)

        assert url in edit_html
        assert mail.outbox[0].subject.startswith("[Prueba]")
        assert mail.outbox[0].to == ["equipo@example.com"]

    def test_test_email_needs_edit_permission(self, client, contact, django_user_model):
        reader = django_user_model.objects.create_user("beto", password="x")
        client.force_login(reader)

        client.post(reverse("orion_form_test_email", args=[contact.pk]))

        assert not mail.outbox


class FailingBackend:
    def __init__(self, *args, **kwargs):
        pass

    def send_messages(self, messages):
        raise ConnectionRefusedError("SMTP down")


class TestFormBlock:
    def _host(self, home_page, form_page):
        stream_block = ContentStreamBlock()
        body = stream_block.clean(
            stream_block.to_python(
                [{"type": "form", "value": {"form_page": form_page.pk}}]
            )
        )
        host = ContentPage(title="Inicio libre", slug="inicio-libre", body=body)
        home_page.add_child(instance=host)
        host.save_revision().publish()
        return host

    def test_submission_from_another_page(self, client, home_page, contact):
        host = self._host(home_page, contact)

        html = client.get(host.url).content.decode()
        response = _send(client, contact, url=host.url)

        assert f'action="{contact.url}"' in html
        assert response.status_code == 200
        assert FormSubmission.objects.get().page_id == contact.pk

    def test_unpublished_form_is_not_shown(self, client, home_page, contact):
        host = self._host(home_page, contact)
        contact.unpublish()

        assert "orion-form" not in client.get(host.url).content.decode()


class TestExampleForms:
    def test_created_once(self, home_page, settings):
        out = io.StringIO()

        call_command("orion_create_example_forms", stdout=out)
        call_command("orion_create_example_forms", stdout=out)

        titles = list(
            FormPage.objects.values_list("title", flat=True).order_by("title")
        )
        assert titles == ["Contacto", "Trabajá con nosotros"]
        jobs = FormPage.objects.get(title="Trabajá con nosotros")
        assert "file" in jobs.form_fields.values_list("field_type", flat=True)
        assert Page.objects.get(pk=jobs.pk).live
        assert "Already exists" in out.getvalue()
