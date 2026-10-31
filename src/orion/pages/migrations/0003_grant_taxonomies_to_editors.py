"""Let Wagtail's editor and moderator groups add and edit categories and tags.

Only adds permissions.
"""

from django.db import migrations

from orion.core.permissions import grant_to_editor_groups, revoke_from_editor_groups

APP_LABEL = "orion_pages"
CODENAMES = [
    "add_articlecategory",
    "change_articlecategory",
    "add_articletag",
    "change_articletag",
]


def grant(apps, schema_editor):
    grant_to_editor_groups(apps, APP_LABEL, CODENAMES)


def revoke(apps, schema_editor):
    revoke_from_editor_groups(apps, APP_LABEL, CODENAMES)


class Migration(migrations.Migration):
    dependencies = [
        ("orion_pages", "0002_replace_welcome_page"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(grant, revoke)]
