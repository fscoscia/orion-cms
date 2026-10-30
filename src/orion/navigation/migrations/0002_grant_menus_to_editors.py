"""Let Wagtail's editor and moderator groups add and edit menus.

Only adds permissions.
"""

from django.db import migrations

from orion.core.permissions import grant_to_editor_groups, revoke_from_editor_groups

APP_LABEL = "orion_navigation"
CODENAMES = ["add_menu", "change_menu"]


def grant(apps, schema_editor):
    grant_to_editor_groups(apps, APP_LABEL, CODENAMES)


def revoke(apps, schema_editor):
    revoke_from_editor_groups(apps, APP_LABEL, CODENAMES)


class Migration(migrations.Migration):
    dependencies = [
        ("orion_navigation", "0001_initial"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(grant, revoke)]
