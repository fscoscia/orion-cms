"""Content operations: writes with permissions, validation and revisions.

They take the acting user as an argument and know nothing about the MCP, HTTP or the
standard streams, so any transport can use them. None publishes, unpublishes, moves or
deletes anything.
"""

from orion.operations.errors import RevisionConflictError
from orion.operations.pages import create_page_draft, update_page_draft
from orion.operations.redirects import create_redirect, update_redirect
from orion.operations.site import update_site_settings, update_site_texts

__all__ = [
    "RevisionConflictError",
    "create_page_draft",
    "create_redirect",
    "update_page_draft",
    "update_redirect",
    "update_site_settings",
    "update_site_texts",
]
