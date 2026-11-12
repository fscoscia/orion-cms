import pytest

from orion.mcp import registry
from orion.mcp.protocol import handle_message

pytestmark = pytest.mark.django_db

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
}


def _names(context):
    return {tool["name"] for tool in registry.list_tools(context)}


def test_every_tool_has_the_level_it_should():
    registry.load_tools()
    levels = {name: tool.access for name, tool in registry._TOOLS.items()}

    for name in READ_TOOLS:
        assert levels[name] == registry.ACCESS_READ, name
    for name in DRAFT_TOOLS:
        assert levels[name] == registry.ACCESS_DRAFT, name
    for name in SETTINGS_TOOLS:
        assert levels[name] == registry.ACCESS_SETTINGS, name


def test_a_read_context_offers_only_read_tools():
    assert _names(registry.READ_ONLY) == READ_TOOLS
    assert _names(registry.ServerContext(access={"read"})) == READ_TOOLS


def test_a_draft_context_offers_read_and_draft_tools():
    context = registry.ServerContext(access={"read", "draft"})

    assert _names(context) == READ_TOOLS | DRAFT_TOOLS


def test_the_local_writing_mode_still_offers_everything():
    context = registry.ServerContext(allow_writes=True)

    assert _names(context) == READ_TOOLS | DRAFT_TOOLS | SETTINGS_TOOLS
    assert context.access == registry.ALL_ACCESS


def test_asking_for_levels_sets_allow_writes():
    assert registry.ServerContext(access={"read"}).allow_writes is False
    assert registry.ServerContext(access={"read", "draft"}).allow_writes is True


@pytest.fixture
def unclassified():
    @registry.tool("test_unclassified", "Forgot its level.", None)
    def forgot():
        return {"ok": True}

    yield
    registry._TOOLS.pop("test_unclassified")


def test_a_tool_without_a_level_is_never_offered(unclassified):
    everything = registry.ServerContext(access=registry.ALL_ACCESS)

    for context in (registry.READ_ONLY, everything):
        assert "test_unclassified" not in _names(context)
        response = handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "test_unclassified"},
            },
            context,
        )
        assert "Unknown tool" in response["error"]["message"]


def test_a_remote_write_can_carry_an_operation_key_and_a_read_cannot():
    remote = registry.ServerContext(access={"read", "draft"}, key=object())

    tools = {tool["name"]: tool for tool in registry.list_tools(remote)}

    assert "operation_key" in tools["page_create_draft"]["inputSchema"]["properties"]
    assert "operation_key" not in tools["page_get"]["inputSchema"]["properties"]
    local = {tool["name"]: tool for tool in registry.list_tools(registry.READ_ONLY)}
    assert "operation_key" not in local["page_get"]["inputSchema"]["properties"]


def test_undoing_a_write_needs_an_api_key():
    local = registry.ServerContext(allow_writes=True)

    assert "settings_revert" not in _names(local)
    assert registry.get_tool(
        "settings_revert",
        registry.ServerContext(access=registry.ALL_ACCESS, key=object()),
    )
