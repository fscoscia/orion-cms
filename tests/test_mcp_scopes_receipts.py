import datetime
import json

import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import Client
from django.utils import timezone
from wagtail.models import Page, PageLogEntry

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.mcp.models import ApiKey, OperationReceipt
from orion.pages.models import ContentPage

pytestmark = [pytest.mark.django_db, pytest.mark.mcp_endpoint]

URL = "/_mcp/"

READ_TOOLS = {
    "site_overview",
    "site_settings",
    "schema",
    "page_tree",
    "page_get",
    "redirects_list",
    "not_found_list",
    "forms_list",
    "conventions_check",
    "unused_images",
    "health",
}
DRAFT_TOOLS = {"page_create_draft", "page_update_draft"}
SETTINGS_TOOLS = {
    "redirect_create",
    "redirect_update",
    "site_settings_update",
    "site_texts_update",
    "settings_revert",
}
ARGUMENTS = {
    "page_create_draft": {"parent_id": 1, "page_type": "x", "fields": {}},
    "page_update_draft": {"id": 1, "expected_revision": 1, "fields": {}},
    "redirect_create": {"old_path": "/a"},
    "redirect_update": {"id": 1},
    "site_settings_update": {"fields": {}},
    "site_texts_update": {"language": "es", "fields": {}},
    "settings_revert": {"reverts": "x"},
}


@pytest.fixture(autouse=True)
def endpoint(settings):
    settings.ORION_MCP_ENDPOINT = True
    settings.ORION_MCP_RATE_LIMIT = 10_000


@pytest.fixture
def make_user(django_user_model):
    def _make(name, group):
        account = django_user_model.objects.create_user(name, password="x")
        account.groups.add(Group.objects.get(name=group))
        return account

    return _make


@pytest.fixture
def editor(make_user):
    return make_user("editor", EDITORS_GROUP)


@pytest.fixture
def administrator(make_user):
    return make_user("administrator", ADMINISTRATORS_GROUP)


def _rpc(token, method, params=None, request_id=1):
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    response = Client().post(
        URL,
        data=json.dumps(message),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200, response.content
    return response.json()


def _call(token, name, **arguments):
    return _rpc(token, "tools/call", {"name": name, "arguments": arguments})


def _data(response):
    result = response["result"]
    assert result["isError"] is False, result
    return json.loads(result["content"][0]["text"])


def _listed(token):
    return {tool["name"] for tool in _rpc(token, "tools/list")["result"]["tools"]}


# Scopes


@pytest.mark.parametrize("account", ["editor", "administrator"])
def test_a_read_only_key_lists_and_calls_only_read_tools(request, account):
    user = request.getfixturevalue(account)
    _, token = ApiKey.issue(name="K", scope="read-only", user=user)

    assert _listed(token) == READ_TOOLS
    for name in DRAFT_TOOLS | SETTINGS_TOOLS:
        error = _call(token, name, **ARGUMENTS[name])["error"]
        assert "Unknown tool" in error["message"], name


@pytest.mark.parametrize("account", ["editor", "administrator"])
def test_a_draft_only_key_adds_only_the_page_drafts(request, account):
    user = request.getfixturevalue(account)
    _, token = ApiKey.issue(name="K", scope="draft-only", user=user)

    assert _listed(token) == READ_TOOLS | DRAFT_TOOLS
    for name in SETTINGS_TOOLS:
        error = _call(token, name, **ARGUMENTS[name])["error"]
        assert "Unknown tool" in error["message"], name


def test_a_key_acts_as_its_user_and_the_work_is_attributed_to_it(editor, home_page):
    _, token = ApiKey.issue(name="K", scope="draft-only", user=editor)

    data = _data(
        _call(
            token,
            "page_create_draft",
            parent_id=home_page.pk,
            page_type="orion_pages.contentpage",
            fields={"title": "Desde la clave"},
        )
    )

    page = Page.objects.get(pk=data["id"])
    assert page.live is False
    assert page.get_latest_revision().user == editor
    assert PageLogEntry.objects.filter(
        page=page, action="wagtail.create", user=editor
    ).exists()


def test_the_users_permissions_still_apply(django_user_model, home_page):
    nobody = django_user_model.objects.create_user("nobody", password="x")
    _, token = ApiKey.issue(name="K", scope="draft-only", user=nobody)

    result = _call(
        token,
        "page_create_draft",
        parent_id=home_page.pk,
        page_type="orion_pages.contentpage",
        fields={"title": "No"},
    )["result"]

    assert result["isError"] is True
    assert "Not allowed" in result["content"][0]["text"]


# Receipts


def _create(token, home_page, title="Una vez", **extra):
    return _call(
        token,
        "page_create_draft",
        parent_id=home_page.pk,
        page_type="orion_pages.contentpage",
        fields={"title": title},
        **extra,
    )


def test_the_same_operation_key_and_arguments_give_the_same_result_once(
    editor, home_page
):
    _, token = ApiKey.issue(name="K", scope="draft-only", user=editor)

    first = _data(_create(token, home_page, operation_key="crear-1"))
    second = _data(_create(token, home_page, operation_key="crear-1"))

    assert second == first
    assert ContentPage.objects.filter(title="Una vez").count() == 1
    assert OperationReceipt.objects.count() == 1


def test_the_same_operation_key_with_other_arguments_is_a_conflict(editor, home_page):
    _, token = ApiKey.issue(name="K", scope="draft-only", user=editor)
    _data(_create(token, home_page, operation_key="crear-1"))

    result = _create(token, home_page, title="Otra", operation_key="crear-1")["result"]

    assert result["isError"] is True
    assert "already used" in result["content"][0]["text"]
    assert not ContentPage.objects.filter(title="Otra").exists()


def test_receipts_belong_to_each_key(editor, home_page):
    _, first_token = ApiKey.issue(name="Uno", scope="draft-only", user=editor)
    _, second_token = ApiKey.issue(name="Dos", scope="draft-only", user=editor)
    _data(_create(first_token, home_page, title="Primera", operation_key="x"))

    second = _data(_create(second_token, home_page, title="Segunda", operation_key="x"))

    assert Page.objects.get(pk=second["id"]).title == "Segunda"
    assert OperationReceipt.objects.count() == 2


def test_a_failed_write_leaves_no_receipt_and_can_be_retried(editor, home_page):
    _, token = ApiKey.issue(name="K", scope="draft-only", user=editor)
    failed = _call(
        token,
        "page_create_draft",
        parent_id=home_page.pk,
        page_type="orion_pages.contentpage",
        fields={"title": "Mal", "live": True},
        operation_key="reintento",
    )["result"]
    assert failed["isError"] is True
    assert not OperationReceipt.objects.exists()

    retried = _create(token, home_page, title="Bien", operation_key="reintento")

    assert _data(retried)["title"] == "Bien"


@pytest.mark.parametrize("bad", ["con espacios", "x" * 101, "ñ"])
def test_an_invalid_operation_key_is_refused(editor, home_page, bad):
    _, token = ApiKey.issue(name="K", scope="draft-only", user=editor)

    response = _create(token, home_page, operation_key=bad)

    assert response["error"]["code"] == -32602


def test_a_read_tool_does_not_take_an_operation_key(editor):
    _, token = ApiKey.issue(name="K", scope="read-only", user=editor)

    response = _call(token, "health", operation_key="x")

    assert response["error"]["code"] == -32602


def test_old_receipts_are_purged_when_a_new_one_is_made(editor, home_page):
    key, token = ApiKey.issue(name="K", scope="draft-only", user=editor)
    old = OperationReceipt.objects.create(
        key=key, tool="t", operation_key="viejo", payload_hash="h", result={}
    )
    OperationReceipt.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - datetime.timedelta(days=31)
    )
    cache.delete("orion_mcp_receipts_purged")

    _data(_create(token, home_page, title="Nueva", operation_key="nueva"))

    assert not OperationReceipt.objects.filter(pk=old.pk).exists()


def test_the_purge_runs_at_most_once_an_hour(editor, home_page):
    key, token = ApiKey.issue(name="K", scope="draft-only", user=editor)
    _data(_create(token, home_page, title="Uno", operation_key="uno"))
    old = OperationReceipt.objects.create(
        key=key, tool="t", operation_key="viejo", payload_hash="h", result={}
    )
    OperationReceipt.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - datetime.timedelta(days=40)
    )

    _data(_create(token, home_page, title="Dos", operation_key="dos"))

    assert OperationReceipt.objects.filter(pk=old.pk).exists()
