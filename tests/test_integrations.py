import smtplib

import pytest
from django.contrib.auth.models import Group
from django.core import mail
from django.core.mail import EmailMessage, get_connection
from django.urls import reverse
from django.utils import timezone

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.forms.models import EmailNotice, FormPage, FormSubmission
from orion.integrations import mail as integrations_mail
from orion.integrations.models import EmailStatus

pytestmark = pytest.mark.django_db

BACKEND = "orion.integrations.mail.EmailBackend"


class FakeSMTP:
    """Stands in for smtplib.SMTP; ``fail_on`` names the step that raises."""

    fail_on = None
    sent = []

    def __init__(self, host, port, **kwargs):
        self._fail("connect")

    def _fail(self, step):
        if self.fail_on == step:
            if step == "login":
                raise smtplib.SMTPAuthenticationError(535, b"Authentication failed")
            raise smtplib.SMTPServerDisconnected(f"{step} failed")

    def starttls(self, **kwargs):
        pass

    def login(self, user, password):
        self._fail("login")

    def sendmail(self, from_email, recipients, message):
        self._fail("send")
        FakeSMTP.sent.append(recipients)

    def quit(self):
        pass

    def close(self):
        pass


@pytest.fixture
def smtp(settings, monkeypatch):
    settings.EMAIL_BACKEND = BACKEND
    settings.EMAIL_HOST = "mail.example.com"
    settings.EMAIL_HOST_USER = "no-responder@example.com"
    settings.EMAIL_HOST_PASSWORD = "secreta-123"
    settings.DEFAULT_FROM_EMAIL = "no-responder@example.com"
    monkeypatch.setattr("django.core.mail.backends.smtp.smtplib.SMTP", FakeSMTP)
    monkeypatch.setattr(FakeSMTP, "fail_on", None)
    monkeypatch.setattr(FakeSMTP, "sent", [])
    return FakeSMTP


def _send(**kwargs):
    return EmailMessage(
        "Consulta", "Datos de Ana", to=["equipo@example.com"], **kwargs
    ).send()


class TestDeliveryRecord:
    def test_success(self, smtp):
        _send()

        status = EmailStatus.load()
        assert status.last_success_at is not None
        assert not status.is_failing

    def test_connection_error(self, smtp):
        smtp.fail_on = "connect"

        with pytest.raises(smtplib.SMTPServerDisconnected):
            _send()

        status = EmailStatus.load()
        assert status.is_failing
        assert status.last_error == "SMTPServerDisconnected: connect failed"

    def test_login_error(self, smtp):
        smtp.fail_on = "login"

        with pytest.raises(smtplib.SMTPAuthenticationError):
            _send()

        assert "Authentication failed" in EmailStatus.load().last_error

    def test_error_while_sending(self, smtp):
        smtp.fail_on = "send"

        with pytest.raises(smtplib.SMTPServerDisconnected):
            _send()

        assert EmailStatus.load().is_failing

    def test_fail_silently(self, smtp):
        smtp.fail_on = "send"

        assert (
            get_connection(fail_silently=True).send_messages(
                [EmailMessage("Consulta", "x", to=["equipo@example.com"])]
            )
            == 0
        )

        assert EmailStatus.load().is_failing

    def test_connection_opened_beforehand(self, smtp):
        # Wagtail's notifications open the connection before sending.
        smtp.fail_on = "connect"
        connection = get_connection()

        with pytest.raises(smtplib.SMTPServerDisconnected):
            connection.open()

        assert EmailStatus.load().is_failing

    def test_recovery_keeps_the_last_error(self, smtp):
        smtp.fail_on = "connect"
        with pytest.raises(smtplib.SMTPServerDisconnected):
            _send()
        smtp.fail_on = None

        _send()

        status = EmailStatus.load()
        assert not status.is_failing
        assert status.last_error

    def test_long_error_is_cut(self, smtp):
        integrations_mail.record_failure("x" * 2000)

        assert len(EmailStatus.load().last_error) == integrations_mail.ERROR_MAX_LENGTH

    def test_keeps_no_recipients_contents_or_password(self, smtp):
        smtp.fail_on = "login"
        with pytest.raises(smtplib.SMTPAuthenticationError):
            _send()

        row = str(EmailStatus.objects.values().get())
        for text in ("equipo@example.com", "Datos de Ana", "secreta-123"):
            assert text not in row

    def test_a_record_error_does_not_stop_the_email(self, smtp, monkeypatch):
        def broken(**kwargs):
            raise RuntimeError("database down")

        monkeypatch.setattr(EmailStatus.objects, "update_or_create", broken)

        assert _send() == 1
        assert smtp.sent == [["equipo@example.com"]]


URL = reverse("orion_integrations")


def _user(django_user_model, name, group_name):
    user = django_user_model.objects.create_user(
        name, email=f"{name}@example.com", password="x"
    )
    user.groups.add(Group.objects.get(name=group_name))
    return user


@pytest.fixture
def administrator(client, django_user_model, home_page):
    client.force_login(_user(django_user_model, "jefa", ADMINISTRATORS_GROUP))
    return client


def _html(client, url=URL):
    return client.get(url).content.decode()


def _status(**fields):
    EmailStatus.objects.update_or_create(pk=1, defaults=fields)


class TestScreen:
    def test_off(self, administrator, settings):
        settings.EMAIL_HOST = ""

        html = _html(administrator)

        assert "Apagado" in html
        assert "quedan en su bandeja" in html
        assert "Crear una casilla" in html

    def test_configured_without_showing_the_password(self, administrator, smtp):
        html = _html(administrator)

        assert "mail.example.com:587" in html
        assert "no-responder@example.com" in html
        assert "Cargada" in html
        assert "secreta-123" not in html
        assert "Sin probar" in html

    def test_server_without_login(self, administrator, smtp, settings):
        settings.EMAIL_HOST_USER = settings.EMAIL_HOST_PASSWORD = ""

        html = _html(administrator)

        assert "Falta" not in html
        assert "Con errores" not in html

    def test_active(self, administrator, smtp):
        _status(last_success_at=timezone.now())

        assert "Activo" in _html(administrator)

    def test_failing_shows_the_error(self, administrator, smtp):
        _status(last_failure_at=timezone.now(), last_error="SMTPAuthenticationError")

        html = _html(administrator)

        assert "Con errores" in html
        assert "SMTPAuthenticationError" in html

    def test_incomplete_settings_are_failing(self, administrator, smtp, settings):
        settings.EMAIL_HOST_PASSWORD = ""
        _status(last_success_at=timezone.now())

        html = _html(administrator)

        assert "Con errores" in html
        assert "EMAIL_HOST_PASSWORD" in html

    def test_own_backend_is_not_tracked(self, administrator, smtp, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        assert "no se registran" in _html(administrator)

    def test_maps(self, administrator):
        html = _html(administrator)

        assert "tile.openstreetmap.org" in html
        assert "no admite tráfico alto" in html

    def test_menu_for_administrators(self, administrator):
        assert '"orion_integrations"' in _html(
            administrator, reverse("wagtailadmin_home")
        )

    def test_editors_have_no_access(self, client, django_user_model, home_page):
        client.force_login(_user(django_user_model, "ana", EDITORS_GROUP))

        assert client.get(URL).status_code != 200
        assert '"orion_integrations"' not in _html(client, reverse("wagtailadmin_home"))


class TestTestEmail:
    def test_sends(self, administrator, smtp):
        response = administrator.post(URL, {"recipient": "jefa@example.com"})

        assert response.status_code == 302
        assert smtp.sent == [["jefa@example.com"]]
        assert "Activo" in _html(administrator)

    def test_failure_is_shown(self, administrator, smtp):
        smtp.fail_on = "login"

        response = administrator.post(
            URL, {"recipient": "jefa@example.com"}, follow=True
        )

        html = response.content.decode()
        assert "No se pudo enviar el email de prueba" in html
        assert "Authentication failed" in html
        assert "Con errores" in html

    def test_defaults_to_the_user_email(self, administrator):
        assert 'value="jefa@example.com"' in _html(administrator)

    def test_invalid_address(self, administrator, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        response = administrator.post(URL, {"recipient": "no-es-email"})

        assert response.status_code == 200
        assert not mail.outbox

    def test_get_does_not_send(self, administrator, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        _html(administrator)

        assert not mail.outbox

    def test_editors_cannot_send(self, client, django_user_model, home_page, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        client.force_login(_user(django_user_model, "ana", EDITORS_GROUP))

        client.post(URL, {"recipient": "ana@example.com"})

        assert not mail.outbox


class TestHomeWarning:
    HOME = reverse("wagtailadmin_home")

    def _pending(self, home_page, count):
        page = FormPage(title="Contacto", slug="contacto", to_address="a@example.com")
        home_page.add_child(instance=page)
        for _number in range(count):
            FormSubmission.objects.create(
                page=page, form_data={}, email_notice=EmailNotice.PENDING
            )

    def test_not_configured_in_production(self, administrator, settings):
        settings.EMAIL_HOST = ""
        settings.DEBUG = False

        html = _html(administrator, self.HOME)

        assert "no hay un servidor de email configurado" in html
        assert URL in html

    def test_failing_with_pending_notices(self, administrator, smtp, home_page):
        _status(last_failure_at=timezone.now(), last_error="x")
        self._pending(home_page, 3)

        html = _html(administrator, self.HOME)

        assert "el último envío falló" in html
        assert "3 envíos de formularios esperan su aviso por email" in html

    def test_nothing_wrong(self, administrator, smtp):
        _status(last_success_at=timezone.now())

        assert "orion-email-warning" not in _html(administrator, self.HOME)

    def test_development_without_smtp(self, administrator, settings):
        settings.EMAIL_HOST = ""
        settings.DEBUG = True

        assert "orion-email-warning" not in _html(administrator, self.HOME)

    def test_editors_do_not_see_it(self, client, django_user_model, smtp, home_page):
        _status(last_failure_at=timezone.now(), last_error="x")
        client.force_login(_user(django_user_model, "ana", EDITORS_GROUP))

        assert "orion-email-warning" not in _html(client, self.HOME)
