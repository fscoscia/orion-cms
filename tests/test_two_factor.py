import re
from base64 import b32encode

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django_otp.oath import totp
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from orion.editor.checks import check_two_factor
from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP

pytestmark = [pytest.mark.django_db, pytest.mark.two_factor]

ADMIN_HOME = "/admin/"


@pytest.fixture
def make_user(django_user_model):
    def _make(username, group_name=EDITORS_GROUP, **fields):
        user = django_user_model.objects.create_user(username, password="x", **fields)
        if group_name:
            user.groups.add(Group.objects.get(name=group_name))
        return user

    return _make


def _code(device):
    return str(
        totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits)
    ).zfill(device.digits)


def _authenticator(user):
    return TOTPDevice.objects.create(user=user, name="authenticator", confirmed=True)


def _backup_codes(user, *codes):
    device = StaticDevice.objects.create(user=user, name="backup")
    for code in codes:
        StaticToken.objects.create(device=device, token=code)
    return device


class TestSetup:
    def test_user_without_device_is_sent_to_setup(self, client, make_user, home_page):
        client.force_login(make_user("ana"))

        response = client.get(ADMIN_HOME)

        assert response.status_code == 302
        assert response["Location"].startswith(reverse("orion_2fa_setup"))

    def test_setup_shows_a_qr_code_and_the_key(self, client, make_user):
        user = make_user("ana")
        client.force_login(user)

        html = client.get(reverse("orion_2fa_setup")).content.decode()

        device = TOTPDevice.objects.get(user=user, confirmed=False)
        secret = b32encode(device.bin_key).decode().rstrip("=")
        grouped = " ".join(secret[i : i + 4] for i in range(0, len(secret), 4))
        assert "<svg" in html
        assert f"secret={secret}" in device.config_url
        assert grouped in html

    def test_confirming_shows_ten_backup_codes_once(self, client, make_user, home_page):
        user = make_user("ana")
        client.force_login(user)
        client.get(reverse("orion_2fa_setup"))
        device = TOTPDevice.objects.get(user=user)

        response = client.post(
            f"{reverse('orion_2fa_setup')}?next={ADMIN_HOME}", {"code": _code(device)}
        )
        codes_page = client.get(response["Location"]).content.decode()
        second_visit = client.get(reverse("orion_2fa_backup_codes"))

        device.refresh_from_db()
        assert device.confirmed
        assert len(re.findall(r"<li><code>[a-z0-9]{8}</code></li>", codes_page)) == 10
        assert StaticToken.objects.filter(device__user=user).count() == 10
        assert second_visit["Location"] == reverse("orion_2fa_manage")
        assert client.get(ADMIN_HOME).status_code == 200

    def test_wrong_setup_code_is_rejected(self, client, make_user):
        user = make_user("ana")
        client.force_login(user)
        client.get(reverse("orion_2fa_setup"))

        response = client.post(reverse("orion_2fa_setup"), {"code": "000000"})

        assert response.status_code == 200
        assert '<li class="error">' in response.content.decode()
        assert not TOTPDevice.objects.get(user=user).confirmed


class TestVerify:
    def test_user_with_device_is_sent_to_verify(self, client, make_user, home_page):
        user = make_user("ana")
        _authenticator(user)
        client.force_login(user)

        response = client.get("/admin/pages/")

        assert response["Location"] == (
            f"{reverse('orion_2fa_verify')}?next=%2Fadmin%2Fpages%2F"
        )

    def test_valid_code_opens_the_admin(self, client, make_user, home_page):
        user = make_user("ana")
        device = _authenticator(user)
        client.force_login(user)

        right = client.post(
            reverse("orion_2fa_verify"), {"code": _code(device), "next": ADMIN_HOME}
        )

        assert right["Location"] == ADMIN_HOME
        assert client.get(ADMIN_HOME).status_code == 200

    def test_wrong_code_is_rejected(self, client, make_user, home_page):
        user = make_user("ana")
        _authenticator(user)
        client.force_login(user)

        response = client.post(reverse("orion_2fa_verify"), {"code": "000000"})

        assert response.status_code == 200
        # The sign-in styles hide field errors; the message must be a visible one.
        assert '<li class="error">' in response.content.decode()
        assert client.get(ADMIN_HOME).status_code != 200

    def test_external_next_is_ignored(self, client, make_user, home_page):
        user = make_user("ana")
        device = _authenticator(user)
        client.force_login(user)

        response = client.post(
            reverse("orion_2fa_verify"),
            {"code": _code(device), "next": "https://evil.example/"},
        )

        assert response["Location"] == reverse("wagtailadmin_home")

    def test_backup_code_works_once(self, client, make_user, home_page):
        user = make_user("ana")
        _authenticator(user)
        _backup_codes(user, "abcd1234")
        client.force_login(user)

        first = client.post(reverse("orion_2fa_verify"), {"code": "abcd 1234"})
        client.logout()
        client.force_login(user)
        second = client.post(reverse("orion_2fa_verify"), {"code": "abcd1234"})

        assert first.status_code == 302
        assert second.status_code == 200

    def test_repeated_wrong_codes_are_slowed_down(self, client, make_user):
        user = make_user("ana")
        device = _authenticator(user)
        client.force_login(user)

        for _attempt in range(3):
            client.post(reverse("orion_2fa_verify"), {"code": "000000"})
        response = client.post(reverse("orion_2fa_verify"), {"code": _code(device)})

        assert response.status_code == 200


class TestScope:
    def test_public_site_does_not_ask(self, client, make_user, home_page):
        user = make_user("ana")
        _authenticator(user)
        client.force_login(user)

        assert client.get("/").status_code == 200

    @pytest.mark.parametrize(
        "url_name",
        ["wagtailadmin_login", "wagtailadmin_javascript_catalog", "orion_admin_colors"],
    )
    def test_open_admin_urls(self, client, make_user, url_name):
        user = make_user("ana")
        _authenticator(user)
        client.force_login(user)

        assert client.get(reverse(url_name)).status_code in (200, 302)
        assert (
            not client.get(reverse(url_name))
            .get("Location", "")
            .startswith(reverse("orion_2fa_verify"))
        )

    def test_requirement_can_be_turned_off(
        self, client, settings, make_user, home_page
    ):
        settings.ORION_2FA_REQUIRED = False
        client.force_login(make_user("ana"))

        assert client.get(ADMIN_HOME).status_code == 200

    def test_check_warns_when_off_without_debug(self, settings):
        settings.DEBUG = False
        settings.ORION_2FA_REQUIRED = False

        assert [message.id for message in check_two_factor(None)] == ["orion.W002"]


class TestManage:
    @pytest.fixture
    def verified_client(self, client, make_user, home_page):
        user = make_user("ana")
        device = _authenticator(user)
        client.force_login(user)
        client.post(reverse("orion_2fa_verify"), {"code": _code(device)})
        client.user = user
        return client

    def test_regenerating_replaces_backup_codes(self, verified_client):
        user = verified_client.user
        _backup_codes(user, "oldcode1")

        response = verified_client.post(
            reverse("orion_2fa_manage"), {"action": "regenerate"}
        )

        tokens = set(
            StaticToken.objects.filter(device__user=user).values_list(
                "token", flat=True
            )
        )
        assert response["Location"] == reverse("orion_2fa_backup_codes")
        assert len(tokens) == 10
        assert "oldcode1" not in tokens

    def test_new_phone_starts_the_setup_again(self, verified_client):
        verified_client.post(reverse("orion_2fa_manage"), {"action": "replace"})

        response = verified_client.get(ADMIN_HOME)

        assert not TOTPDevice.objects.filter(user=verified_client.user).exists()
        assert response["Location"].startswith(reverse("orion_2fa_setup"))


class TestReset:
    def _verified(self, client, user):
        device = _authenticator(user)
        client.force_login(user)
        client.post(reverse("orion_2fa_verify"), {"code": _code(device)})

    def test_administrator_resets_an_editor(self, client, make_user, home_page):
        administrator = make_user("jefa", ADMINISTRATORS_GROUP)
        editor = make_user("ana")
        _authenticator(editor)
        self._verified(client, administrator)

        users_page = client.get(reverse("wagtailusers_users:index")).content.decode()
        response = client.post(reverse("orion_2fa_reset", args=[editor.pk]))

        assert reverse("orion_2fa_reset", args=[editor.pk]) in users_page
        assert response.status_code == 302
        assert not TOTPDevice.objects.filter(user=editor).exists()

    def test_editor_cannot_reset(self, client, make_user, home_page):
        editor = make_user("ana")
        other = make_user("beto")
        self._verified(client, editor)

        _authenticator(other)

        response = client.post(reverse("orion_2fa_reset", args=[other.pk]))

        # Wagtail turns a permission error in its admin views into a redirect.
        assert response.status_code in (302, 403)
        assert TOTPDevice.objects.filter(user=other).exists()

    def test_administrator_cannot_reset_a_superuser(
        self, client, make_user, admin_user, home_page
    ):
        administrator = make_user("jefa", ADMINISTRATORS_GROUP)
        _authenticator(admin_user)
        self._verified(client, administrator)

        response = client.post(reverse("orion_2fa_reset", args=[admin_user.pk]))

        assert response.status_code in (302, 403)
        assert TOTPDevice.objects.filter(user=admin_user).exists()
