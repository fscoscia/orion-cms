import datetime
import re

import pytest
from axes.models import AccessAttempt, AccessLog
from django.contrib.auth.models import Group
from django.core import mail
from django.core.management import call_command
from django.test import Client, RequestFactory
from django.urls import reverse

from orion.core.client_ip import get_client_ip
from orion.editor.roles import EDITORS_GROUP

pytestmark = pytest.mark.django_db

PASSWORD = "clave-Segura-2026"
LOGIN = reverse("wagtailadmin_login")
ADMIN_HOME = reverse("wagtailadmin_home")


@pytest.fixture
def ana(django_user_model):
    user = django_user_model.objects.create_user(
        "ana",
        email="ana@example.com",
        password=PASSWORD,
        first_name="Ana",
        last_name="Pérez",
    )
    user.groups.add(Group.objects.get(name=EDITORS_GROUP))
    return user


def _login(client, password, username="ana", ip="10.0.0.1"):
    return client.post(
        LOGIN,
        {"username": username, "password": password, "next": ADMIN_HOME},
        REMOTE_ADDR=ip,
    )


def _fail(client, times, **kwargs):
    for _attempt in range(times):
        _login(client, "equivocada", **kwargs)


class TestClientIp:
    def _ip(self, settings, proxies, forwarded=None):
        settings.ORION_TRUSTED_PROXIES = proxies
        extra = {"REMOTE_ADDR": "127.0.0.1"}
        if forwarded is not None:
            extra["HTTP_X_FORWARDED_FOR"] = forwarded
        return get_client_ip(RequestFactory().get("/", **extra))

    def test_without_proxies_the_header_is_ignored(self, settings):
        assert self._ip(settings, 0, "1.2.3.4") == "127.0.0.1"

    def test_behind_one_proxy(self, settings):
        assert self._ip(settings, 1, "1.2.3.4") == "1.2.3.4"

    def test_addresses_written_by_the_visitor_are_ignored(self, settings):
        assert self._ip(settings, 1, "9.9.9.9, 1.2.3.4") == "1.2.3.4"

    def test_two_proxies(self, settings):
        assert self._ip(settings, 2, "9.9.9.9, 1.2.3.4, 10.0.0.2") == "1.2.3.4"

    def test_short_header(self, settings):
        assert self._ip(settings, 2, "1.2.3.4") == "1.2.3.4"

    def test_missing_header(self, settings):
        assert self._ip(settings, 1) == "127.0.0.1"


class TestLockout:
    def test_fifth_failure_locks_even_the_right_password(self, client, ana):
        _fail(client, 5)

        response = _login(client, PASSWORD)

        assert response.status_code == 429
        html = response.content.decode()
        assert "Demasiados intentos" in html
        assert "15 minutos" in html

    def test_four_failures_do_not_lock(self, client, ana):
        _fail(client, 4)

        assert _login(client, PASSWORD).status_code == 302

    def test_success_clears_the_failures(self, client, ana):
        _fail(client, 4)
        _login(client, PASSWORD)
        client.logout()

        _fail(client, 4)

        assert _login(client, PASSWORD).status_code == 302

    def test_other_address_still_signs_in(self, client, ana):
        _fail(client, 5)

        assert _login(client, PASSWORD, ip="10.0.0.2").status_code == 302

    def test_other_user_from_the_same_address(self, client, ana, django_user_model):
        django_user_model.objects.create_superuser("beto", password=PASSWORD)
        _fail(client, 5)

        assert _login(client, PASSWORD, username="beto").status_code == 302

    def test_lock_expires(self, client, ana):
        _fail(client, 5)
        AccessAttempt.objects.update(
            attempt_time=AccessAttempt.objects.get().attempt_time
            - datetime.timedelta(minutes=16)
        )

        assert _login(client, PASSWORD).status_code == 302

    def test_unlock_by_command(self, client, ana):
        _fail(client, 5)

        call_command("axes_reset_username", "ana")

        assert _login(client, PASSWORD).status_code == 302

    def test_limits_come_from_the_settings(self, client, ana, settings):
        settings.AXES_FAILURE_LIMIT = 2
        _fail(client, 2)

        assert _login(client, PASSWORD).status_code == 429

    def test_behind_a_proxy_the_real_address_counts(self, client, ana, settings):
        settings.ORION_TRUSTED_PROXIES = 1
        for _attempt in range(5):
            client.post(
                LOGIN,
                {"username": "ana", "password": "equivocada"},
                REMOTE_ADDR="127.0.0.1",
                HTTP_X_FORWARDED_FOR="1.1.1.1",
            )

        response = client.post(
            LOGIN,
            {"username": "ana", "password": PASSWORD, "next": ADMIN_HOME},
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_FORWARDED_FOR="2.2.2.2",
        )

        assert response.status_code == 302
        assert AccessAttempt.objects.get().ip_address == "1.1.1.1"

    def test_no_record_of_each_sign_in(self, client, ana):
        _login(client, PASSWORD)

        assert not AccessLog.objects.exists()


class TestPasswordReset:
    @pytest.fixture(autouse=True)
    def _email(self, settings):
        settings.WAGTAIL_PASSWORD_RESET_ENABLED = True
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

    def _link(self):
        return re.search(r"https?://[^/]+(/\S+)", mail.outbox[0].body).group(1)

    def test_link_on_the_login(self, client):
        html = client.get(LOGIN).content.decode()

        assert reverse("wagtailadmin_password_reset") in html

    def test_hidden_when_disabled(self, client, settings):
        settings.WAGTAIL_PASSWORD_RESET_ENABLED = False

        html = client.get(LOGIN).content.decode()

        assert reverse("wagtailadmin_password_reset") not in html

    def test_recovery_and_single_use(self, client, ana):
        client.post(
            reverse("wagtailadmin_password_reset"), {"email": "ana@example.com"}
        )
        link = self._link()

        form_url = client.get(link).url
        done = client.post(
            form_url,
            {"new_password1": "otra-Clave-2026", "new_password2": "otra-Clave-2026"},
        )
        again = client.get(link, follow=True)

        assert done.status_code == 302
        ana.refresh_from_db()
        assert ana.check_password("otra-Clave-2026")
        assert 'name="new_password1"' not in again.content.decode()

    def test_unknown_email_sends_nothing(self, client, ana):
        response = client.post(
            reverse("wagtailadmin_password_reset"), {"email": "nadie@example.com"}
        )

        assert response.status_code == 302
        assert not mail.outbox

    @pytest.mark.two_factor
    def test_second_factor_still_required(self, client, ana):
        from django_otp.plugins.otp_totp.models import TOTPDevice

        TOTPDevice.objects.create(user=ana, name="authenticator", confirmed=True)
        client.post(
            reverse("wagtailadmin_password_reset"), {"email": "ana@example.com"}
        )
        form_url = client.get(self._link()).url
        client.post(
            form_url,
            {"new_password1": "otra-Clave-2026", "new_password2": "otra-Clave-2026"},
        )

        _login(client, "otra-Clave-2026")
        response = client.get(ADMIN_HOME)

        assert response.status_code == 302
        assert response.url.startswith(reverse("orion_2fa_verify"))


def _account_data(client):
    """Every field of the account page as it is, ready to post."""
    response = client.get(reverse("wagtailadmin_account"))
    data = {}
    for panels in response.context["panels_by_tab"].values():
        for panel in panels:
            form = panel.get_form()
            for field in form:
                value = field.value()
                if not value or hasattr(value, "url"):
                    continue
                data[field.html_name] = value
    return data


class TestSessions:
    @pytest.fixture
    def browsers(self, ana):
        first, second = Client(), Client()
        for browser in (first, second):
            browser.force_login(ana)
            assert browser.get(ADMIN_HOME).status_code == 200
        return first, second

    def test_own_email_change_keeps_this_session(self, browsers, ana):
        first, second = browsers
        data = _account_data(first)
        data["name_email-email"] = "ana.nueva@example.com"

        response = first.post(reverse("wagtailadmin_account"), data)

        assert response.status_code == 302
        ana.refresh_from_db()
        assert ana.email == "ana.nueva@example.com"
        assert first.get(ADMIN_HOME).status_code == 200
        assert second.get(ADMIN_HOME).url.startswith(LOGIN)

    def test_change_by_someone_else_signs_out_every_session(self, browsers, ana):
        ana.email = "ana.nueva@example.com"
        ana.save()

        for browser in browsers:
            assert browser.get(ADMIN_HOME).url.startswith(LOGIN)

    def test_password_change_keeps_this_session(self, browsers, ana):
        first, second = browsers
        data = _account_data(first)
        data.update(
            {
                "password-old_password": PASSWORD,
                "password-new_password1": "otra-Clave-2026",
                "password-new_password2": "otra-Clave-2026",
            }
        )

        first.post(reverse("wagtailadmin_account"), data)

        assert first.get(ADMIN_HOME).status_code == 200
        assert second.get(ADMIN_HOME).url.startswith(LOGIN)

    def test_sessions_from_before_are_kept(self, client, ana):
        client.force_login(ana)
        session = client.session
        session.pop("orion_email_hash", None)
        session.save()

        assert client.get(ADMIN_HOME).status_code == 200
        assert "orion_email_hash" in client.session
