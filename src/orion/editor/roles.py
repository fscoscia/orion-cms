"""The admin roles of an Orion site: Editors prepare content, Administrators approve it.

They are Wagtail's default groups, renamed by the migration ``orion_editor.0001_roles``.
"""

EDITORS_GROUP = "Editores"
ADMINISTRATORS_GROUP = "Administradores"


def is_site_administrator(user):
    """Whether the user is an Administrator of the site (or a superuser)."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=ADMINISTRATORS_GROUP).exists()
