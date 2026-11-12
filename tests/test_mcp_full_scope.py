import json

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from wagtail.contrib.redirects.models import Redirect

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.mcp.models import ApiKey, OperationReceipt
from orion.site_data.models import SiteSettings, SiteTexts

pytestmark = [pytest.mark.django_db, pytest.mark.mcp_endpoint]

URL = "/_mcp/"


@pytest.fixture(autouse=True)
def endpoint(settings):
    settings.ORION_MCP_ENDPOINT = True
    settings.ORION_MCP_RATE_LIMIT = 10_000


def _user(django_user_model, name, group):
    account = django_user_model.objects.create_user(name, password="x")
    account.groups.add(Group.objects.get(name=group))
    return account


@pytest.fixture
def administrator(django_user_model):
    return _user(django_user_model, "administrator", ADMINISTRATORS_GROUP)


@pytest.fixture
def editor(django_user_model):
    return _user(django_user_model, "editor", EDITORS_GROUP)


@pytest.fixture
def token(administrator):
    return ApiKey.issue(name="Completa", scope="full", user=administrator)[1]


def _call(token, name, **arguments):
    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    response = Client().post(
        URL,
        data=json.dumps(message),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200, response.content
    return response.json()


def _data(response):
    result = response["result"]
    assert result["isError"] is False, result
    return json.loads(result["content"][0]["text"])


def _error(response):
    result = response["result"]
    assert result["isError"] is True, result
    return result["content"][0]["text"]


def test_a_full_key_lists_every_level_and_the_revert_tool(token):
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    response = Client().post(
        URL,
        data=json.dumps(message),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    names = {tool["name"] for tool in response.json()["result"]["tools"]}

    assert {
        "page_create_draft",
        "redirect_create",
        "redirect_update",
        "site_settings_update",
        "site_texts_update",
        "settings_revert",
    } <= names
    assert not {n for n in names if "publish" in n or "delete" in n}


def test_a_full_key_creates_a_redirect_as_its_user(token, administrator):
    data = _data(
        _call(
            token,
            "redirect_create",
            old_path="/viejo",
            redirect_link="https://example.org/",
        )
    )

    assert (
        Redirect.objects.get(old_path="/viejo").redirect_link == "https://example.org/"
    )
    assert data["operation_key"]


def test_a_full_key_of_an_editor_cannot_write_settings(django_user_model, editor):
    token = ApiKey.issue(name="E", scope="full", user=editor)[1]

    text = _error(
        _call(
            token,
            "redirect_create",
            old_path="/x",
            redirect_link="https://example.org/",
        )
    )

    assert "Not allowed" in text
    assert not Redirect.objects.exists()


def test_a_settings_write_keeps_only_the_changed_fields(token):
    SiteSettings.objects.create(phone="111", email="a@example.com")

    data = _data(
        _call(
            token,
            "site_settings_update",
            fields={"phone": "222", "email": "a@example.com"},
        )
    )

    receipt = OperationReceipt.objects.get(operation_key=data["operation_key"])
    assert receipt.before["values"] == {"phone": "111"}


def test_a_given_operation_key_is_kept_and_retried_once(token):
    SiteSettings.objects.create(phone="111")

    first = _data(
        _call(token, "site_settings_update", fields={"phone": "222"}, operation_key="a")
    )
    second = _data(
        _call(token, "site_settings_update", fields={"phone": "222"}, operation_key="a")
    )

    assert first == second
    assert first["operation_key"] == "a"
    assert OperationReceipt.objects.count() == 1


def test_a_settings_write_can_be_reverted(token):
    SiteSettings.objects.create(phone="111")
    data = _data(_call(token, "site_settings_update", fields={"phone": "222"}))

    _data(_call(token, "settings_revert", reverts=data["operation_key"]))

    assert SiteSettings.objects.get().phone == "111"


def test_reverting_texts_and_redirects(token, administrator):
    from wagtail.models import Locale

    SiteTexts.objects.create(locale=Locale.get_default(), tagline="Antes")
    code = Locale.get_default().language_code
    texts = _data(
        _call(token, "site_texts_update", language=code, fields={"tagline": "Despues"})
    )
    redirect = Redirect.objects.create(
        old_path="/a", redirect_link="https://example.org/a"
    )
    moved = _data(
        _call(
            token,
            "redirect_update",
            id=redirect.pk,
            redirect_link="https://example.org/b",
        )
    )

    _data(_call(token, "settings_revert", reverts=texts["operation_key"]))
    _data(_call(token, "settings_revert", reverts=moved["operation_key"]))

    assert SiteTexts.objects.get().tagline == "Antes"
    redirect.refresh_from_db()
    assert redirect.redirect_link == "https://example.org/a"


def test_a_change_made_afterwards_is_a_conflict(token):
    settings_row = SiteSettings.objects.create(phone="111")
    data = _data(_call(token, "site_settings_update", fields={"phone": "222"}))
    SiteSettings.objects.filter(pk=settings_row.pk).update(phone="333")

    text = _error(_call(token, "settings_revert", reverts=data["operation_key"]))

    assert "changed" in text
    assert SiteSettings.objects.get().phone == "333"


def test_reverting_twice_says_so_and_writes_nothing(token):
    SiteSettings.objects.create(phone="111")
    data = _data(_call(token, "site_settings_update", fields={"phone": "222"}))
    _data(_call(token, "settings_revert", reverts=data["operation_key"]))
    SiteSettings.objects.update(phone="444")

    again = _data(_call(token, "settings_revert", reverts=data["operation_key"]))

    assert again["already_reverted"] is True
    assert SiteSettings.objects.get().phone == "444"


def test_a_created_redirect_is_not_reverted_nor_deleted(token):
    data = _data(
        _call(
            token,
            "redirect_create",
            old_path="/nuevo",
            redirect_link="https://example.org/",
        )
    )

    text = _error(_call(token, "settings_revert", reverts=data["operation_key"]))

    assert "admin" in text
    assert Redirect.objects.filter(old_path="/nuevo").exists()


def test_an_unknown_or_purged_operation_cannot_be_reverted(token):
    text = _error(_call(token, "settings_revert", reverts="no-existe"))

    assert "cannot be reverted" in text


def test_a_receipt_of_another_key_cannot_be_reverted(token, administrator):
    SiteSettings.objects.create(phone="111")
    data = _data(_call(token, "site_settings_update", fields={"phone": "222"}))
    other = ApiKey.issue(name="Otra", scope="full", user=administrator)[1]

    text = _error(_call(other, "settings_revert", reverts=data["operation_key"]))

    assert "cannot be reverted" in text
    assert SiteSettings.objects.get().phone == "222"


def test_the_revert_checks_the_users_permission(token, administrator):
    SiteSettings.objects.create(phone="111")
    data = _data(_call(token, "site_settings_update", fields={"phone": "222"}))
    administrator.groups.clear()

    text = _error(_call(token, "settings_revert", reverts=data["operation_key"]))

    assert "Not allowed" in text
    assert SiteSettings.objects.get().phone == "222"
