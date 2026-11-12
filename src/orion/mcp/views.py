"""The MCP endpoint of the site: one JSON-RPC message per POST, with an API key."""

import json
import logging

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from orion.core.client_ip import get_client_ip
from orion.mcp import auth, limits
from orion.mcp.models import Scope
from orion.mcp.protocol import (
    PARSE_ERROR,
    SUPPORTED_PROTOCOL_VERSIONS,
    error_response,
    handle_message,
)
from orion.mcp.registry import (
    ACCESS_DRAFT,
    ACCESS_READ,
    ACCESS_SETTINGS,
    ServerContext,
)

logger = logging.getLogger(__name__)

ACCESS_BY_SCOPE = {
    Scope.READ_ONLY: frozenset({ACCESS_READ}),
    Scope.DRAFT_ONLY: frozenset({ACCESS_READ, ACCESS_DRAFT}),
    Scope.FULL: frozenset({ACCESS_READ, ACCESS_DRAFT, ACCESS_SETTINGS}),
}


def _answer(response, status=200, **headers):
    """Nothing about this endpoint is ever stored by a cache."""
    response.status_code = status
    response["Cache-Control"] = "no-store"
    for name, value in headers.items():
        response[name.replace("_", "-")] = value
    return response


def _problem(status, message, **headers):
    return _answer(JsonResponse({"error": message}), status, **headers)


def _context_for(key):
    return ServerContext(access=ACCESS_BY_SCOPE[key.scope], actor=key.user, key=key)


def _log_call(key, message, response):
    """One line per call: the key's prefix, what was called and whether it worked.
    Never the token or the arguments."""
    method = message.get("method") if isinstance(message, dict) else None
    params = message.get("params") if isinstance(message, dict) else None
    tool = (
        params.get("name")
        if method == "tools/call" and isinstance(params, dict)
        else None
    )
    failed = response is not None and (
        "error" in response or response.get("result", {}).get("isError") is True
    )
    logger.info(
        "mcp key=%s call=%s result=%s",
        key.prefix,
        tool or method,
        "error" if failed else "ok",
    )


@csrf_exempt
def mcp_endpoint(request):
    if not settings.ORION_MCP_ENDPOINT:
        raise Http404
    if request.method != "POST":
        return _problem(405, "Use POST.", Allow="POST")

    origin = request.headers.get("Origin")
    if origin and origin not in settings.ORION_MCP_ALLOWED_ORIGINS:
        return _problem(403, "This origin is not allowed.")
    version = request.headers.get("MCP-Protocol-Version")
    if version and version not in SUPPORTED_PROTOCOL_VERSIONS:
        return _problem(400, "Unsupported MCP protocol version.")

    address = get_client_ip(request)
    wait = limits.failed_auth_blocked_for(address)
    if wait:
        return _problem(429, "Too many failed attempts.", Retry_After=wait)

    try:
        declared = int(request.META.get("CONTENT_LENGTH") or 0)
    except ValueError:
        declared = 0
    if declared > settings.ORION_MCP_MAX_BODY:
        return _problem(413, "The request is too large.")

    key = auth.authenticate(request)
    if key is None:
        limits.record_failed_auth(address)
        return _problem(
            401,
            "Invalid or missing API key.",
            WWW_Authenticate='Bearer realm="orion-mcp"',
        )
    wait = limits.rate_limited_for(key)
    if wait:
        return _problem(429, "Too many requests.", Retry_After=wait)
    auth.record_use(key)

    body = request.body
    if len(body) > settings.ORION_MCP_MAX_BODY:
        return _problem(413, "The request is too large.")
    try:
        message = json.loads(body)
    except ValueError:
        return _answer(
            JsonResponse(error_response(None, PARSE_ERROR, "Parse error.")), 400
        )

    response = handle_message(message, _context_for(key))
    _log_call(key, message, response)
    if response is None:
        return _answer(HttpResponse(), 202)
    return _answer(JsonResponse(response))
