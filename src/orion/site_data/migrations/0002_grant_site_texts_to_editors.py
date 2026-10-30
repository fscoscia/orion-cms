"""Let Wagtail's editor and moderator groups edit the translatable site texts.

Only adds permissions; the fixed site data keeps its own settings permission.
"""

from django.db import migrations

from orion.core.permissions import grant_to_editor_groups, revoke_from_editor_groups

APP_LABEL = "orion_site_data"
CODENAMES = ["add_sitetexts", "change_sitetexts"]


def grant(apps, schema_editor):
    grant_to_editor_groups(apps, APP_LABEL, CODENAMES)


def revoke(apps, schema_editor):
    revoke_from_editor_groups(apps, APP_LABEL, CODENAMES)


class Migration(migrations.Migration):
    dependencies = [
        ("orion_site_data", "0001_initial"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(grant, revoke)]
