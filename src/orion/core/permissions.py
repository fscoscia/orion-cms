"""Helpers for data migrations that grant permissions to Wagtail's default groups."""

from django.contrib.auth.management import create_permissions

EDITOR_GROUP_NAMES = ("Editors", "Moderators")


def grant_to_editor_groups(apps, app_label, codenames):
    """Give the editor and moderator groups the given permissions of ``app_label``.

    Permissions are normally created after all migrations run, so they are created
    here first. Groups that do not exist are skipped.
    """
    app_config = apps.get_app_config(app_label)
    app_config.models_module = True
    create_permissions(app_config, apps=apps, verbosity=0)
    app_config.models_module = None

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
