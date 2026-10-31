"""Administrators manage redirects (wagtail.contrib.redirects); Editors do not."""

from django.db import migrations

from orion.core.permissions import ensure_permissions

ADMINISTRATORS = "Administradores"
CODENAMES = ["add_redirect", "change_redirect", "delete_redirect"]


def _permissions(apps):
    return apps.get_model("auth", "Permission").objects.filter(
        content_type__app_label="wagtailredirects", codename__in=CODENAMES
    )


def forwards(apps, schema_editor):
    administrators = (
        apps.get_model("auth", "Group").objects.filter(name=ADMINISTRATORS).first()
    )
    if administrators is None:
        return
    ensure_permissions(apps, "wagtailredirects")
    administrators.permissions.add(*_permissions(apps))


def backwards(apps, schema_editor):
    administrators = (
        apps.get_model("auth", "Group").objects.filter(name=ADMINISTRATORS).first()
    )
    if administrators is not None:
        administrators.permissions.remove(*_permissions(apps))


class Migration(migrations.Migration):
    dependencies = [
        ("orion_editor", "0002_previewlink"),
        ("wagtailredirects", "0008_add_verbose_name_plural"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
