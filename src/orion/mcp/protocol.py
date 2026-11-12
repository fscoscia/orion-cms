"""The MCP messages (JSON-RPC 2.0) the server understands, without any transport.

`handle_message` takes one decoded message and returns the response to send, or None
when no response is due (notifications). It never reads or writes a stream.

Only the revisions of the protocol that open with an ``initialize`` handshake are
supported. The newest revision (2026-07-28) drops that handshake; see design.md of
add-local-readonly-mcp.
"""

import json
import logging

from django.core.serializers.json import DjangoJSONEncoder

from orion import __version__
from orion.mcp import receipts
from orion.mcp.registry import (
    READ_ONLY,
    InvalidArgumentsError,
    ToolError,
    UnknownToolError,
    get_tool,
    list_tools,
    validate_arguments,
)

logger = logging.getLogger(__name__)

# Newest first. The tools subset the server implements is the same in all of them.
SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def error_response(request_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _valid_id(value):
    return isinstance(value, str) or (
        isinstance(value, int) and not isinstance(value, bool)
    )


def handle_message(message, context=READ_ONLY):
    if not isinstance(message, dict):
        return error_response(None, INVALID_REQUEST, "Invalid request.")
    if "method" not in message:
        # A response to a request of the server. It sends none, so ignore it.
        if "result" in message or "error" in message:
            return None
        return error_response(None, INVALID_REQUEST, "Invalid request.")
    if "id" not in message:
        return None  # A notification never gets a response.

    request_id = message["id"]
    method = message["method"]
    params = message.get("params", {})
    if (
        message.get("jsonrpc") != "2.0"
        or not _valid_id(request_id)
        or not isinstance(method, str)
        or not isinstance(params, dict)
    ):
        return error_response(None, INVALID_REQUEST, "Invalid request.")

    handlers = {
        "initialize": _initialize,
        "ping": lambda params: {},
        "tools/list": lambda params: {"tools": list_tools(context)},
        "tools/call": lambda params: _call_tool(params, context),
    }
    handler = handlers.get(method)
    if handler is None:
        return error_response(request_id, METHOD_NOT_FOUND, f"Unknown method: {method}")
    try:
        result = handler(params)
    except RpcError as error:
        return error_response(request_id, error.code, error.message)
    except Exception:
        logger.exception("The server failed while handling %s.", method)
        return error_response(request_id, INTERNAL_ERROR, "Internal error.")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _initialize(params):
    requested = params.get("protocolVersion")
    version = (
        requested
        if requested in SUPPORTED_PROTOCOL_VERSIONS
        else SUPPORTED_PROTOCOL_VERSIONS[0]
    )
    return {
        "protocolVersion": version,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "orion", "version": __version__},
    }


def _call_tool(params, context):
    name = params.get("name")
    arguments = params.get("arguments", {})
    try:
        tool = get_tool(name, context)
        validate_arguments(tool.schema_for(context), arguments)
    except (UnknownToolError, InvalidArgumentsError) as error:
        raise RpcError(INVALID_PARAMS, str(error)) from None
    arguments = dict(arguments)
    operation_key = arguments.pop("operation_key", None)

    tracked = tool.name in receipts.TRACKED_TOOLS and context.key is not None
    if tracked and operation_key is None:
        operation_key = receipts.new_operation_key()

    def run():
        if not tool.writes:
            return tool.function(**arguments)
        data = tool.function(context=context, **arguments)
        if tracked:
            data = {**data, "operation_key": operation_key}
        return data

    try:
        if operation_key is not None and tool.writes and context.key is not None:
            data = receipts.run_once(
                context.key,
                tool.name,
                operation_key,
                arguments,
                run,
                undo=lambda: context.undo.get("record"),
            )
        else:
            data = run()
    except ToolError as error:
        return _text_result(str(error), is_error=True)
    except Exception:
        logger.exception("The tool %s failed.", name)
        return _text_result(
            "The tool failed unexpectedly. The details are in the server log.",
            is_error=True,
        )
    return _text_result(
        json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False), is_error=False
    )


def _text_result(text, is_error):
    return {"content": [{"type": "text", "text": text}], "isError": is_error}
