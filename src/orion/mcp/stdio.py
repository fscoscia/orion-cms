"""The stdio transport: one JSON-RPC message per line in, one per line out."""

import contextlib
import json
import sys

from orion.mcp.protocol import PARSE_ERROR, error_response, handle_message
from orion.mcp.registry import READ_ONLY


def serve(input_stream, output_stream, before_message=None, context=READ_ONLY):
    """Answer the messages of `input_stream` until it is closed.

    Only responses are written to `output_stream`. Anything a tool prints goes to the
    error output instead, so it cannot break the protocol.
    """
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        if before_message is not None:
            before_message()
        try:
            message = json.loads(line)
        except ValueError:
            response = error_response(None, PARSE_ERROR, "Parse error.")
        else:
            with contextlib.redirect_stdout(sys.stderr):
                response = handle_message(message, context)
        if response is not None:
            output_stream.write(json.dumps(response) + "\n")
            output_stream.flush()
