from django.core.management.base import BaseCommand, CommandError

from orion.mcp.agent import AGENT_USERNAME, AgentAccountError, create_agent_user


class Command(BaseCommand):
    help = (
        f"Create the technical account `{AGENT_USERNAME}` that the MCP server writes "
        "as with --allow-writes: an Editor with no usable password, so nobody can "
        "log in with it. An account that already exists is left as it is."
    )

    def handle(self, *args, **options):
        try:
            user, created = create_agent_user()
        except AgentAccountError as error:
            raise CommandError(str(error)) from error
        groups = ", ".join(user.groups.values_list("name", flat=True)) or "no groups"
        if created:
            self.stdout.write(f"Created {AGENT_USERNAME} (groups: {groups}).")
            return
        if user.is_superuser:
            raise CommandError(
                f"{AGENT_USERNAME} exists and is a superuser. Fix it in the admin: "
                "this command does not change an existing account."
            )
        self.stdout.write(
            f"{AGENT_USERNAME} already exists (groups: {groups}); nothing changed."
        )
