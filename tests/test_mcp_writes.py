import io
import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.models.signals import post_delete
from django.test.utils import CaptureQueriesContext
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, PageLogEntry

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.mcp import protocol, registry
from orion.mcp.agent import AGENT_USERNAME, create_agent_user
from orion.mcp.protocol import handle_message
from orion.pages.models import ContentPage
from orion.site_data.models import SiteSettings

pytestmark = pytest.mark.django_db


@pytest.fixture
def agent():
    user, _ = create_agent_user()
    return user


@pytest.fixture
def context(agent):
    return registry.ServerContext(allow_writes=True, actor=agent)


@pytest.fixture
def agent_as_administrator(agent):
    agent.groups.add(Group.objects.get(name=ADMINISTRATORS_GROUP))
    return agent


@pytest.fixture
def published_page(home_page):
    page = home_page.add_child(instance=ContentPage(title="Nosotros", slug="nosotros"))
    page.save_revision().publish()
    return page


def _request(method, params=None, context=registry.READ_ONLY):
    message = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        message["params"] = params
    return handle_message(message, context)


def _call(name, context, **arguments):
    response = _request("tools/call", {"name": name, "arguments": arguments}, context)
    assert "error" not in response, response
    result = response["result"]
    text = result["content"][0]["text"]
    return text if result["isError"] else json.loads(text)


def _failed(name, context, **arguments):
    response = _request("tools/call", {"name": name, "arguments": arguments}, context)
    assert response["result"]["isError"] is True, response
    return response["result"]["content"][0]["text"]


# The technical account


def test_the_command_creates_the_account(django_user_model):
    out = io.StringIO()

    call_command("orion_create_agent_user", stdout=out)

    user = django_user_model.objects.get(username=AGENT_USERNAME)
    assert user.is_active
    assert not user.is_superuser
    assert not user.is_staff
    assert user.email == ""
    assert not user.has_usable_password()
    assert list(user.groups.values_list("name", flat=True)) == [EDITORS_GROUP]
    assert "Created" in out.getvalue()


def test_nobody_can_log_in_with_the_account(agent):
    assert not agent.has_usable_password()
    for password in ("", "x", "orion-agent", "!", None):
        assert agent.check_password(password) is False


def test_running_the_command_again_changes_nothing(django_user_model, agent):
    agent.groups.add(Group.objects.get(name=ADMINISTRATORS_GROUP))
    agent.is_active = False
    agent.save()
    out = io.StringIO()

    call_command("orion_create_agent_user", stdout=out)

    agent.refresh_from_db()
    assert agent.is_active is False
    assert set(agent.groups.values_list("name", flat=True)) == {
        EDITORS_GROUP,
        ADMINISTRATORS_GROUP,
    }
    assert "already exists" in out.getvalue()
    assert django_user_model.objects.filter(username=AGENT_USERNAME).count() == 1


def test_an_existing_superuser_account_is_an_error_and_is_not_changed(
    django_user_model,
):
    user = django_user_model.objects.create_superuser(AGENT_USERNAME, password="x")

    with pytest.raises(CommandError):
        call_command("orion_create_agent_user", stdout=io.StringIO())

    user.refresh_from_db()
    assert user.is_superuser
    assert user.has_usable_password()


def test_the_installer_does_not_create_the_account(monkeypatch, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ORION_FORMS_PRIVATE_ROOT = str(tmp_path / "private")
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "admin")
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "a-strong-password-123")

    call_command("orion_install", "--noinput")

    assert not get_user_model().objects.filter(username=AGENT_USERNAME).exists()


# The flags of orion_mcp


@pytest.fixture
def run_server(monkeypatch):
    def _run(*args):
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        err = io.StringIO()
        call_command("orion_mcp", *args, stderr=err)
        return err.getvalue()

    return _run


def test_writing_without_the_account_is_an_error_that_names_the_command(run_server):
    with pytest.raises(CommandError, match="orion_create_agent_user"):
        run_server("--allow-writes")


def test_writing_with_an_inactive_account_is_an_error(run_server, agent):
    agent.is_active = False
    agent.save()

    with pytest.raises(CommandError, match="not active"):
        run_server("--allow-writes")


def test_writing_as_a_superuser_account_is_an_error(run_server, agent):
    agent.is_superuser = True
    agent.save()

    with pytest.raises(CommandError, match="superuser"):
        run_server("--allow-writes")


def test_the_server_says_who_it_writes_as_and_with_which_groups(run_server, agent):
    message = run_server("--allow-writes")

    assert f"Writing as {AGENT_USERNAME}" in message
    assert EDITORS_GROUP in message


def test_without_the_flag_the_account_is_not_needed(run_server):
    assert run_server() == ""


# Write tools only exist with the flag

WRITE_TOOLS = {
    "page_create_draft",
    "page_update_draft",
    "redirect_create",
    "redirect_update",
    "site_settings_update",
    "site_texts_update",
}


def test_write_tools_are_not_listed_without_the_flag():
    names = {tool["name"] for tool in _request("tools/list")["result"]["tools"]}

    assert not names & WRITE_TOOLS


def test_write_tools_are_listed_with_the_flag(context):
    names = {
        tool["name"]
        for tool in _request("tools/list", context=context)["result"]["tools"]
    }

    assert names >= WRITE_TOOLS


def test_calling_a_write_tool_without_the_flag_is_an_unknown_tool():
    response = _request("tools/call", {"name": "page_update_draft", "arguments": {}})

    assert response["error"]["code"] == protocol.INVALID_PARAMS
    assert "Unknown tool" in response["error"]["message"]


# The write tools


def test_a_draft_is_created_through_the_tool(context, agent, home_page):
    data = _call(
        "page_create_draft",
        context,
        parent_id=home_page.pk,
        page_type="orion_pages.contentpage",
        fields={"title": "Servicios"},
    )

    page = Page.objects.get(pk=data["id"])
    assert data["live"] is False
    assert data["latest_revision_id"] == page.latest_revision_id
    assert page.get_latest_revision().user == agent


def test_a_draft_is_updated_with_the_revision_read_from_the_page(
    context, published_page
):
    revision = _call("page_get", context, id=published_page.pk)["latest_revision_id"]

    data = _call(
        "page_update_draft",
        context,
        id=published_page.pk,
        expected_revision=revision,
        fields={"title": "Quiénes somos"},
    )

    assert data["live"] is True
    assert data["latest_revision_id"] != revision
    assert Page.objects.get(pk=published_page.pk).title == "Nosotros"


def test_a_stale_revision_is_an_error_that_asks_to_read_again(context, published_page):
    stale = published_page.latest_revision_id
    _call(
        "page_update_draft",
        context,
        id=published_page.pk,
        expected_revision=stale,
        fields={"title": "Uno"},
    )

    message = _failed(
        "page_update_draft",
        context,
        id=published_page.pk,
        expected_revision=stale,
        fields={"title": "Dos"},
    )

    assert "Read the page again" in message


def test_an_invalid_field_is_an_error_with_the_cause(context, home_page):
    message = _failed(
        "page_create_draft",
        context,
        parent_id=home_page.pk,
        page_type="orion_pages.contentpage",
        fields={"title": "X", "live": True},
    )

    assert message.startswith("Not valid")
    assert "live" in message


def test_an_unknown_page_type_is_an_error(context, home_page):
    message = _failed(
        "page_create_draft",
        context,
        parent_id=home_page.pk,
        page_type="nope.nope",
        fields={"title": "X"},
    )

    assert "Unknown page type" in message


def test_an_editor_account_cannot_write_redirects_or_site_data(context):
    redirect = _failed(
        "redirect_create",
        context,
        old_path="/a",
        redirect_link="https://example.com/b",
    )
    data = _failed("site_settings_update", context, fields={"phone": "1"})

    assert redirect.startswith("Not allowed")
    assert data.startswith("Not allowed")
    assert not Redirect.objects.exists()


def test_an_editor_account_can_write_the_site_texts(context):
    data = _call(
        "site_texts_update", context, language="es", fields={"tagline": "Hola"}
    )

    assert data["tagline"] == "Hola"


def test_with_the_account_in_administrators_redirects_and_site_data_work(
    agent_as_administrator,
):
    context = registry.ServerContext(allow_writes=True, actor=agent_as_administrator)

    redirect = _call(
        "redirect_create",
        context,
        old_path="/a",
        redirect_link="https://example.com/b",
    )
    updated = _call("redirect_update", context, id=redirect["id"], is_permanent=False)
    data = _call("site_settings_update", context, fields={"phone": "+595 21 000 000"})

    assert redirect["is_permanent"] is True
    assert updated["is_permanent"] is False
    assert data["phone"] == "+595 21 000 000"
    assert SiteSettings.objects.get().phone == "+595 21 000 000"


def test_page_get_gives_the_revision_to_expect(published_page):
    data = _call("page_get", registry.READ_ONLY, id=published_page.pk)

    assert data["latest_revision_id"] == published_page.latest_revision_id


# Guarantees with writing on


def test_with_writing_on_nothing_is_published_deleted_or_attributed_to_anyone_else(
    agent_as_administrator, home_page, published_page
):
    context = registry.ServerContext(allow_writes=True, actor=agent_as_administrator)
    deleted = []

    def count(sender, **kwargs):
        deleted.append(sender)

    post_delete.connect(count, dispatch_uid="test_mcp_writes_deletions")
    live_before = set(Page.objects.filter(live=True).values_list("pk", flat=True))
    logs_before = set(PageLogEntry.objects.values_list("pk", flat=True))
    try:
        with CaptureQueriesContext(connection) as queries:
            draft = _call(
                "page_create_draft",
                context,
                parent_id=home_page.pk,
                page_type="orion_pages.contentpage",
                fields={"title": "Borrador"},
            )
            _call(
                "page_update_draft",
                context,
                id=published_page.pk,
                expected_revision=published_page.latest_revision_id,
                fields={"title": "Nosotros 2"},
            )
            redirect = _call(
                "redirect_create",
                context,
                old_path="/a",
                redirect_link="https://example.com/b",
            )
            _call("redirect_update", context, id=redirect["id"], is_permanent=False)
            _call("site_settings_update", context, fields={"phone": "1"})
            _call("site_texts_update", context, language="es", fields={"tagline": "t"})
    finally:
        post_delete.disconnect(dispatch_uid="test_mcp_writes_deletions")

    assert (
        set(Page.objects.filter(live=True).values_list("pk", flat=True)) == live_before
    )
    assert Page.objects.get(pk=draft["id"]).live is False
    assert deleted == []
    assert not [
        query["sql"]
        for query in queries.captured_queries
        if query["sql"].lstrip().upper().startswith("DELETE")
    ]
    authors = set(
        PageLogEntry.objects.exclude(pk__in=logs_before).values_list(
            "user__username", flat=True
        )
    )
    assert authors == {AGENT_USERNAME}  # every new entry, none without an author


def test_write_results_do_not_expose_accounts(context, home_page):
    data = _call(
        "page_create_draft",
        context,
        parent_id=home_page.pk,
        page_type="orion_pages.contentpage",
        fields={"title": "Borrador"},
    )
    page = _call("page_get", context, id=data["id"])

    assert AGENT_USERNAME not in json.dumps(data) + json.dumps(page)
    assert "owner" not in page
