"""The tools the server offers, defined apart from any transport.

A tool is a name, a description, a JSON schema for its arguments and a function that
only reads. Another transport (HTTP, later) can reuse this module as it is.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100

OPERATION_KEY = {
    "type": "string",
    "maxLength": 100,
    "pattern": "^[A-Za-z0-9_.:-]+$",
    "description": "Makes a retry safe: the same key and arguments give one result.",
}

PAGING_PROPERTIES = {
    "page": {"type": "integer", "minimum": 1},
    "per_page": {"type": "integer", "minimum": 1, "maximum": MAX_PER_PAGE},
}


ACCESS_READ = "read"
ACCESS_DRAFT = "draft"
ACCESS_SETTINGS = "settings"
READ_ACCESS = frozenset({ACCESS_READ})
ALL_ACCESS = frozenset({ACCESS_READ, ACCESS_DRAFT, ACCESS_SETTINGS})


@dataclass(frozen=True)
class ServerContext:
    """What a server run allows and who acts.

    `access` is the set of levels of tools it may offer: reading only, unless asked
    otherwise. `allow_writes` is the older way to ask for every level. `key` is the API
    key of a remote call, when there is one.
    """

    allow_writes: bool = False
    actor: Any = None
    access: Any = None
    key: Any = None
    # A settings tool puts here what it changed, so the receipt can keep it.
    undo: dict = field(default_factory=dict, compare=False, repr=False)

    def __post_init__(self):
        if self.access is None:
            level = ALL_ACCESS if self.allow_writes else READ_ACCESS
            object.__setattr__(self, "access", level)
        else:
            object.__setattr__(self, "access", frozenset(self.access))
        object.__setattr__(self, "allow_writes", bool(self.access - READ_ACCESS))


READ_ONLY = ServerContext()


class ToolError(Exception):
    """A failure the assistant can read and act on, not a crash of the server."""


class InvalidArgumentsError(Exception):
    """The arguments of a call do not match the tool's input schema."""


class UnknownToolError(Exception):
    """The call names a tool that does not exist."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    function: Callable[..., Any]
    access: str | None = None
    needs_key: bool = False

    @property
    def writes(self):
        return self.access != ACCESS_READ

    def allowed_in(self, context):
        """A tool without a known access level is never offered."""
        if self.needs_key and context.key is None:
            return False  # e.g. undoing a write needs the receipts of an API key
        return self.access in ALL_ACCESS and self.access in context.access

    def schema_for(self, context):
        """The arguments of a call; a remote write can carry an operation key."""
        if self.access == ACCESS_READ or context.key is None:
            return self.input_schema
        properties = {**self.input_schema["properties"], "operation_key": OPERATION_KEY}
        return {**self.input_schema, "properties": properties}

    def describe(self, context=None):
        schema = self.input_schema if context is None else self.schema_for(context)
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": schema,
        }


_TOOLS: dict[str, Tool] = {}


def tool(
    name,
    description,
    access,
    properties=None,
    required=(),
    paged=False,
    needs_key=False,
):
    """Register the decorated function as a tool; it receives the arguments by name.

    `access` is the level of the tool: `read`, `draft` or `settings`. A tool that is not
    `read` only exists when the context allows its level, and also receives the server
    `context`.
    """
    properties = dict(properties or {})
    if paged:
        properties.update(PAGING_PROPERTIES)

    def register(function):
        _TOOLS[name] = Tool(
            name=name,
            description=description,
            input_schema={
                "type": "object",
                "properties": properties,
                "required": list(required),
                "additionalProperties": False,
            },
            function=function,
            access=access,
            needs_key=needs_key,
        )
        return function

    return register


def load_tools():
    """Import the modules that register the tools."""
    from orion.mcp import tools_diagnostics, tools_site, tools_write  # noqa: F401


def list_tools(context=READ_ONLY):
    load_tools()
    return [
        registered.describe(context)
        for registered in _TOOLS.values()
        if registered.allowed_in(context)
    ]


def get_tool(name, context=READ_ONLY):
    load_tools()
    try:
        found = _TOOLS[name]
    except (KeyError, TypeError):
        raise UnknownToolError(f"Unknown tool: {name}") from None
    if not found.allowed_in(context):
        raise UnknownToolError(f"Unknown tool: {name}")
    return found


_TYPES = {
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "string": lambda value: isinstance(value, str),
    "boolean": lambda value: isinstance(value, bool),
    "object": lambda value: isinstance(value, dict),
}


def validate_arguments(schema, arguments):
    """Check the arguments against the small subset of JSON schema the tools use."""
    if not isinstance(arguments, dict):
        raise InvalidArgumentsError("The arguments must be an object.")
    properties = schema["properties"]
    for key in arguments:
        if key not in properties:
            raise InvalidArgumentsError(f"Unknown argument: {key}")
    for key in schema["required"]:
        if key not in arguments:
            raise InvalidArgumentsError(f"Missing argument: {key}")
    for key, value in arguments.items():
        rules = properties[key]
        if not _TYPES[rules["type"]](value):
            raise InvalidArgumentsError(f"{key} must be of type {rules['type']}.")
        if "minimum" in rules and value < rules["minimum"]:
            raise InvalidArgumentsError(f"{key} must be at least {rules['minimum']}.")
        if "maximum" in rules and value > rules["maximum"]:
            raise InvalidArgumentsError(f"{key} must be at most {rules['maximum']}.")
        if "maxLength" in rules and len(value) > rules["maxLength"]:
            raise InvalidArgumentsError(f"{key} is too long.")
        if "pattern" in rules and not re.search(rules["pattern"], value):
            raise InvalidArgumentsError(f"{key} has characters that are not allowed.")
        if "enum" in rules and value not in rules["enum"]:
            raise InvalidArgumentsError(f"{key} must be one of {rules['enum']}.")
    return arguments


def paginate(items, arguments, serialize=lambda item: item):
    """Return one bounded page of a queryset or list, with the total."""
    page = arguments.get("page", 1)
    per_page = arguments.get("per_page", DEFAULT_PER_PAGE)
    total = len(items) if isinstance(items, list) else items.count()
    start = (page - 1) * per_page
    return {
        "items": [serialize(item) for item in items[start : start + per_page]],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": start + per_page < total,
    }
