"""Editors and Administrators manage promoted search results."""

from django.db import migrations

from orion.core.permissions import ensure_permissions

GROUPS = ["Editores", "Administradores"]
CODENAMES = ["add_searchpromotion", "change_searchpromotion", "delete_searchpromotion"]


def _permissions(apps):
    return apps.get_model("auth", "Permission").objects.filter(
        content_type__app_label="wagtailsearchpromotions", codename__in=CODENAMES
    )


def forwards(apps, schema_editor):
    groups = apps.get_model("auth", "Group").objects.filter(name__in=GROUPS)
    if not groups.exists():
        return
    ensure_permissions(apps, "wagtailsearchpromotions")
    permissions = list(_permissions(apps))
    for group in groups:
        group.permissions.add(*permissions)


def backwards(apps, schema_editor):
    permissions = list(_permissions(apps))
    for group in apps.get_model("auth", "Group").objects.filter(name__in=GROUPS):
        group.permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [
        ("orion_editor", "0003_redirect_permissions"),
        ("wagtailsearchpromotions", "0008_query_verbose_name"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
