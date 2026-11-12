import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from wagtail.models import Site

from orion import __version__
from orion.forms.models import FormField, FormPage, FormSubmission
from orion.mcp import protocol, registry
from orion.mcp.protocol import handle_message
from orion.mcp.stdio import serve
from orion.pages.models import ContentPage
from orion.seo.models import NotFoundPath

pytestmark = pytest.mark.django_db

ROOT = Path(__file__).resolve().parent.parent


def _request(method, params=None, request_id=1):
    message = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        message["params"] = params
    return handle_message(message)


def _call(name, **arguments):
    response = _request("tools/call", {"name": name, "arguments": arguments})
    result = response["result"]
    text = result["content"][0]["text"]
    return json.loads(text) if not result["isError"] else text


# Protocol


def test_initialize_answers_with_the_version_and_the_tools_capability():
    response = _request("initialize", {"protocolVersion": "2025-06-18"})

    result = response["result"]
    assert response["id"] == 1
    assert result["protocolVersion"] == "2025-06-18"
    assert result["capabilities"] == {"tools": {}}
    assert result["serverInfo"] == {"name": "orion", "version": __version__}


def test_initialize_offers_its_newest_version_for_an_unknown_one():
    result = _request("initialize", {"protocolVersion": "1999-01-01"})["result"]

    assert result["protocolVersion"] == protocol.SUPPORTED_PROTOCOL_VERSIONS[0]


def test_ping_answers_an_empty_result():
    assert _request("ping")["result"] == {}


def test_tools_list_describes_every_tool():
    tools = _request("tools/list")["result"]["tools"]

    names = {tool["name"] for tool in tools}
    assert {"site_overview", "schema", "page_tree", "page_get", "health"} <= names
    for tool in tools:
        assert tool["description"]
        assert tool["inputSchema"]["type"] == "object"


def test_a_notification_gets_no_response():
    message = {"jsonrpc": "2.0", "method": "notifications/initialized"}

    assert handle_message(message) is None


def test_an_unknown_method_is_an_error():
    error = _request("resources/list")["error"]

    assert error["code"] == protocol.METHOD_NOT_FOUND


@pytest.mark.parametrize(
    "message",
    [
        [],
        "ping",
        {"jsonrpc": "1.0", "id": 1, "method": "ping"},
        {"jsonrpc": "2.0", "id": 1, "method": 7},
        {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": []},
        {"jsonrpc": "2.0", "id": True, "method": "ping"},
    ],
)
def test_an_invalid_request_is_an_error(message):
    response = handle_message(message)

    assert response["error"]["code"] == protocol.INVALID_REQUEST


def test_an_unknown_tool_is_a_protocol_error():
    error = _request("tools/call", {"name": "delete_everything"})["error"]

    assert error["code"] == protocol.INVALID_PARAMS
    assert "Unknown tool" in error["message"]


# Registry


def test_per_page_above_the_maximum_is_rejected():
    error = _request(
        "tools/call", {"name": "page_tree", "arguments": {"per_page": 500}}
    )["error"]

    assert error["code"] == protocol.INVALID_PARAMS
    assert "per_page" in error["message"]


def test_an_unknown_argument_is_rejected():
    error = _request("tools/call", {"name": "health", "arguments": {"force": True}})[
        "error"
    ]

    assert error["code"] == protocol.INVALID_PARAMS


def test_the_registry_works_without_any_stream():
    tool = registry.get_tool("health")

    assert tool.function() == {"status": "ok"}


@pytest.fixture
def broken_tools():
    @registry.tool("test_expected_failure", "Fails with a message.", "read")
    def expected():
        raise registry.ToolError("Nothing to see here.")

    @registry.tool("test_crash", "Crashes.", "read")
    def crash():
        raise RuntimeError("secret detail")

    @registry.tool("test_noisy", "Prints to the standard output.", "read")
    def noisy():
        print("noise that would break the protocol")  # noqa: T201
        return {"ok": True}

    yield
    for name in ("test_expected_failure", "test_crash", "test_noisy"):
        registry._TOOLS.pop(name)


def test_a_tool_error_is_an_answer_not_a_crash(broken_tools):
    result = _request("tools/call", {"name": "test_expected_failure"})["result"]

    assert result["isError"] is True
    assert result["content"][0]["text"] == "Nothing to see here."


def test_an_unexpected_failure_hides_its_details(broken_tools):
    result = _request("tools/call", {"name": "test_crash"})["result"]

    assert result["isError"] is True
    assert "secret detail" not in result["content"][0]["text"]


# Stdio


def _serve(lines, **options):
    output = io.StringIO()
    serve(io.StringIO("\n".join(lines) + "\n"), output, **options)
    return [json.loads(line) for line in output.getvalue().splitlines()]


def test_serve_answers_one_line_per_request():
    responses = _serve(
        [
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            "",
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}),
        ]
    )

    assert [response["id"] for response in responses] == [1, 2]


def test_serve_answers_a_parse_error_and_keeps_going():
    responses = _serve(
        ["{not json", json.dumps({"jsonrpc": "2.0", "id": 3, "method": "ping"})]
    )

    assert responses[0]["error"]["code"] == protocol.PARSE_ERROR
    assert responses[1]["id"] == 3


def test_a_tool_that_prints_does_not_reach_the_protocol_output(broken_tools, capsys):
    call = {"name": "test_noisy"}
    responses = _serve(
        [
            json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": call}
            )
        ]
    )

    assert json.loads(responses[0]["result"]["content"][0]["text"]) == {"ok": True}
    assert "noise" in capsys.readouterr().err


def test_the_command_runs_as_a_subprocess_over_stdio():
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]
    result = subprocess.run(  # noqa: S603
        [sys.executable, "manage.py", "orion_mcp"],
        cwd=ROOT / "example",
        input="\n".join(json.dumps(message) for message in messages) + "\n",
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "example.settings"},
        check=False,
    )

    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert [response["id"] for response in responses] == [1, 2]
    assert responses[0]["result"]["serverInfo"]["name"] == "orion"
    assert responses[1]["result"]["tools"]


# Tools


@pytest.fixture
def site(home_page):
    site = Site.objects.get(is_default_site=True)
    site.site_name = "Clínica Ejemplo"
    site.save()
    return site


@pytest.fixture
def pages(home_page):
    services = home_page.add_child(
        instance=ContentPage(title="Servicios", slug="servicios")
    )
    services.save_revision().publish()
    draft = home_page.add_child(
        instance=ContentPage(title="Borrador", slug="borrador", live=False)
    )
    return services, draft


def test_site_overview_lists_the_languages(site, english_locale):
    data = _call("site_overview")

    assert data["site_name"] == "Clínica Ejemplo"
    assert data["orion_version"] == __version__
    by_code = {language["code"]: language for language in data["languages"]}
    assert by_code[data["base_language"]]["is_public"] is True
    assert by_code["en"]["is_public"] is False


def test_the_schema_lists_the_page_types_and_their_blocks():
    data = _call("schema")

    types = {page_type["type"]: page_type for page_type in data["page_types"]}
    assert "orion_pages.contentpage" in types
    body = next(
        field
        for field in types["orion_pages.contentpage"]["fields"]
        if field["name"] == "body"
    )
    blocks = data["stream_blocks"][body["stream_block"]]
    assert {"hero", "text", "cards"} <= {block["name"] for block in blocks}
    assert (
        "orion_pages.homepage" in types["orion_pages.contentpage"]["parent_page_types"]
    )


def test_the_schema_is_small_until_a_block_is_asked_for():
    assert len(json.dumps(_call("schema"))) < 30_000


def test_the_schema_describes_one_block_in_full():
    data = _call("schema", block="hero")

    definition = next(iter(data["definitions"].values()))
    assert definition["name"] == "hero"
    assert definition["children"]


def test_the_schema_of_an_unknown_block_is_a_tool_error():
    result = _request("tools/call", {"name": "schema", "arguments": {"block": "nope"}})[
        "result"
    ]

    assert result["isError"] is True


def test_page_tree_lists_pages_with_their_state(pages):
    services, draft = pages

    data = _call("page_tree")

    by_id = {item["id"]: item for item in data["items"]}
    assert by_id[services.pk]["live"] is True
    assert by_id[services.pk]["type"] == "orion_pages.contentpage"
    assert by_id[services.pk]["parent_id"] == services.get_parent().pk
    assert by_id[draft.pk]["live"] is False
    assert data["total"] >= 3


def test_page_tree_filters_by_publication(pages):
    services, draft = pages

    data = _call("page_tree", live=False)

    assert [item["id"] for item in data["items"]] == [draft.pk]


def test_page_get_returns_the_fields_and_the_stored_body(pages):
    services, _ = pages

    data = _call("page_get", id=services.pk)

    assert data["title"] == "Servicios"
    assert data["type"] == "orion_pages.contentpage"
    assert data["body"] == []
    assert "owner" not in data


def test_page_get_of_a_missing_page_is_a_tool_error_and_the_server_goes_on():
    result = _request("tools/call", {"name": "page_get", "arguments": {"id": 99999}})[
        "result"
    ]

    assert result["isError"] is True
    assert "99999" in result["content"][0]["text"]
    assert _request("ping")["result"] == {}


def test_site_settings_returns_the_data_and_the_texts(site):
    data = _call("site_settings")

    assert "site_data" in data
    assert isinstance(data["site_texts"], list)


def test_redirects_and_not_found_paths_are_listed(site):
    from wagtail.contrib.redirects.models import Redirect

    Redirect.objects.create(old_path="/viejo", redirect_link="https://example.com/")
    for path, hits in [("/a", 1), ("/b", 9), ("/c", 4)]:
        NotFoundPath.objects.create(site=site, path=path, hits=hits)

    redirects = _call("redirects_list")
    not_found = _call("not_found_list")

    assert [item["old_path"] for item in redirects["items"]] == ["/viejo"]
    assert [item["path"] for item in not_found["items"]] == ["/b", "/c", "/a"]


def test_pagination_reports_the_total_and_whether_there_is_more(site):
    for number in range(5):
        NotFoundPath.objects.create(site=site, path=f"/p{number}", hits=number)

    data = _call("not_found_list", per_page=2, page=2)

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["has_more"] is True


def _form(home_page):
    form = FormPage(
        title="Contacto",
        slug="contacto",
        subject="Consulta",
        to_address="equipo@example.com",
        form_fields=[
            FormField(label="Nombre", field_type="singleline", required=True),
            FormField(label="Mensaje", field_type="multiline", required=True),
        ],
    )
    home_page.add_child(instance=form)
    form.save_revision().publish()
    return form


def test_forms_are_listed_without_their_submissions(home_page):
    form = _form(home_page)
    FormSubmission.objects.create(
        page=form, form_data={"nombre": "Marta Pérez", "mensaje": "Hola reservada"}
    )

    data = _call("forms_list")

    assert data["items"][0]["title"] == "Contacto"
    assert [field["label"] for field in data["items"][0]["fields"]] == [
        "Nombre",
        "Mensaje",
    ]
    text = json.dumps(data)
    assert "Marta" not in text
    assert "reservada" not in text


def test_unused_images_are_listed_and_not_deleted(site, tmp_path, settings):
    from wagtail.images.models import Image
    from wagtail.images.tests.utils import get_test_image_file

    settings.MEDIA_ROOT = tmp_path
    Image.objects.create(title="Sin uso", file=get_test_image_file())

    data = _call("unused_images")

    assert [item["title"] for item in data["items"]] == ["Sin uso"]
    assert Image.objects.count() == 1


def test_health_and_conventions_report(site):
    assert _call("health") == {"status": "ok"}
    assert _call("conventions_check")["total"] >= 0


# Guarantees

ALL_TOOLS = None


def _all_tool_calls(pages_fixture=None):
    return [
        ("site_overview", {}),
        ("site_settings", {}),
        ("schema", {}),
        ("page_tree", {}),
        ("page_get", {"id": 1}),
        ("redirects_list", {}),
        ("not_found_list", {}),
        ("forms_list", {}),
        ("conventions_check", {}),
        ("unused_images", {}),
        ("health", {}),
    ]


def test_every_registered_tool_is_covered_by_the_guarantee_tests():
    registered = {tool["name"] for tool in registry.list_tools()}

    assert registered == {name for name, _ in _all_tool_calls()}


def test_no_tool_writes_to_the_database(pages, home_page, site, english_locale):
    _form(home_page)
    calls = _all_tool_calls()
    calls[4] = ("page_get", {"id": pages[0].pk})

    with CaptureQueriesContext(connection) as queries:
        for name, arguments in calls:
            result = _request("tools/call", {"name": name, "arguments": arguments})
            assert "error" not in result, (name, result)

    writes = [
        query["sql"]
        for query in queries.captured_queries
        if query["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert writes == []


def test_no_tool_exposes_accounts_or_submissions(pages, home_page, site):
    user = get_user_model().objects.create_superuser(
        username="marta.administradora",
        email="marta@secreta.example",
        password="x",  # noqa: S106
        first_name="Marta",
        last_name="Gómez",
    )
    form = _form(home_page)
    FormSubmission.objects.create(
        page=form, form_data={"nombre": "Visitante Anónimo", "mensaje": "Texto privado"}
    )
    page = pages[0]
    page.owner = user
    page.save()
    calls = _all_tool_calls()
    calls[4] = ("page_get", {"id": page.pk})

    everything = ""
    for name, arguments in calls:
        everything += json.dumps(
            _request("tools/call", {"name": name, "arguments": arguments})
        )

    for secret in (
        "marta.administradora",
        "marta@secreta",
        "Gómez",
        "Visitante",
        "privado",
    ):
        assert secret not in everything
