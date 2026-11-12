from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class McpConfig(AppConfig):
    name = "orion.mcp"
    label = "orion_mcp"
    verbose_name = _("Orion MCP server")
