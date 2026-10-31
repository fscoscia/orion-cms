"""Helpers for data migrations that grant permissions to Wagtail's default groups."""

from django.contrib.auth.management import create_permissions

# Orion's role groups, and Wagtail's names for them before orion_editor renames them.
EDITOR_GROUP_NAMES = ("Editores", "Administradores", "Editors", "Moderators")


def ensure_permissions(apps, app_label):
    """Create the permissions of ``app_label`` during migrations.

    Django normally creates them after all migrations run.
    """
    app_config = apps.get_app_config(app_label)
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None


def grant_to_editor_groups(apps, app_label, codenames):
    """Give the editor and moderator groups the given permissions of ``app_label``.

    Groups that do not exist are skipped.
    """
    ensure_permissions(apps, app_label)

    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")
    permissions = permission_model.objects.filter(
        content_type__app_label=app_label, codename__in=codenames
    )
    for group in group_model.objects.filter(name__in=EDITOR_GROUP_NAMES):
        group.permissions.add(*permissions)


def revoke_from_editor_groups(apps, app_label, codenames):
    """Undo :func:`grant_to_editor_groups`."""
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")
    permissions = permission_model.objects.filter(
        content_type__app_label=app_label, codename__in=codenames
    )
    for group in group_model.objects.filter(name__in=EDITOR_GROUP_NAMES):
        group.permissions.remove(*permissions)
