import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from orion.mcp.agent import AgentAccountError, check_agent_user
from orion.mcp.registry import READ_ONLY, ServerContext
from orion.mcp.stdio import serve


class Command(BaseCommand):
    help = (
        "Run an MCP server over standard input and output, so an AI assistant can look "
        "at this site. It only reads unless --allow-writes is given. Logs go to the "
        "error output."
    )
    # Checks would only add noise to the first seconds of the connection.
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-writes",
            action="store_true",
            help=(
                "Also offer the tools that write drafts, redirects and site settings. "
                "They act as the technical account orion-agent, with its permissions."
            ),
        )

    def handle(self, *args, **options):
        context = READ_ONLY
        if options["allow_writes"]:
            try:
                actor = check_agent_user()
            except AgentAccountError as error:
                raise CommandError(str(error)) from error
            groups = ", ".join(actor.groups.values_list("name", flat=True)) or "none"
            self.stderr.write(
                f"Writing as {actor.get_username()} (groups: {groups}). "
                "Nothing is published or deleted."
            )
            context = ServerContext(allow_writes=True, actor=actor)
        serve(
            sys.stdin, sys.stdout, before_message=close_old_connections, context=context
        )
