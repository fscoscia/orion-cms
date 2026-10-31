"""Turn Wagtail's default groups into Orion's roles.

Renames "Editors" to "Editores", "Moderators" to "Administradores" and the
"Moderators approval" workflow and task, keeping their users and permissions; groups that
were already renamed, or whose new name exists, are left alone. Administrators also get
the permissions to manage content, site data, languages and users, but not sites,
collections, workflows or groups. Nothing is removed.
"""

from django.db import migrations
from django.db.models import Q

from orion.core.permissions import ensure_permissions

GROUP_RENAMES = {"Editors": "Editores", "Moderators": "Administradores"}
WORKFLOW_RENAMES = {"Moderators approval": "Aprobación de administradores"}
ADMINISTRATORS = "Administradores"
ADMINISTRATOR_PERMISSIONS = [
    ("orion_navigation", "delete_menu"),
    ("orion_site_data", "delete_sitetexts"),
    ("orion_site_data", "change_sitesettings"),
    ("orion_localization", "change_languagesettings"),
    ("orion_pages", "delete_articlecategory"),
    ("orion_pages", "delete_articletag"),
    ("wagtailcore", "add_locale"),
    ("wagtailcore", "change_locale"),
    ("wagtailcore", "delete_locale"),
    ("auth", "add_user"),
    ("auth", "change_user"),
    ("auth", "delete_user"),
]
ADMINISTRATOR_PAGE_PERMISSIONS = ["bulk_delete_page"]


def _permissions(apps, pairs):
    permission_model = apps.get_model("auth", "Permission")
    query = Q()
    for app_label, codename in pairs:
        query |= Q(content_type__app_label=app_label, codename=codename)
    return permission_model.objects.filter(query)


def _rename(model, renames):
    for old_name, new_name in renames.items():
        if not model.objects.filter(name=new_name).exists():
            model.objects.filter(name=old_name).update(name=new_name)


def forwards(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    _rename(group_model, GROUP_RENAMES)
    _rename(apps.get_model("wagtailcore", "Workflow"), WORKFLOW_RENAMES)
    _rename(apps.get_model("wagtailcore", "Task"), WORKFLOW_RENAMES)

    administrators = group_model.objects.filter(name=ADMINISTRATORS).first()
    if administrators is None:
        return
    for app_label in {app_label for app_label, _ in ADMINISTRATOR_PERMISSIONS} | {
        "wagtailcore"
    }:
        ensure_permissions(apps, app_label)
    administrators.permissions.add(*_permissions(apps, ADMINISTRATOR_PERMISSIONS))

    root_page = apps.get_model("wagtailcore", "Page").objects.filter(depth=1).first()
    if root_page is not None:
        page_permission_model = apps.get_model("wagtailcore", "GroupPagePermission")
        for permission in _permissions(
            apps, [("wagtailcore", code) for code in ADMINISTRATOR_PAGE_PERMISSIONS]
        ):
            page_permission_model.objects.get_or_create(
                group=administrators, page=root_page, permission=permission
            )


def backwards(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    administrators = group_model.objects.filter(name=ADMINISTRATORS).first()
    if administrators is not None:
        administrators.permissions.remove(
            *_permissions(apps, ADMINISTRATOR_PERMISSIONS)
        )
        apps.get_model("wagtailcore", "GroupPagePermission").objects.filter(
            group=administrators,
            permission__codename__in=ADMINISTRATOR_PAGE_PERMISSIONS,
        ).delete()
    reverse = {new: old for old, new in GROUP_RENAMES.items()}
    _rename(group_model, reverse)
    workflow_reverse = {new: old for old, new in WORKFLOW_RENAMES.items()}
    _rename(apps.get_model("wagtailcore", "Workflow"), workflow_reverse)
    _rename(apps.get_model("wagtailcore", "Task"), workflow_reverse)


class Migration(migrations.Migration):
    # After every Wagtail migration that looks the groups up by their original names
    # to grant permissions (admin access, images, documents).
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
        ("wagtailadmin", "0006_formstate"),
        ("wagtailimages", "0027_image_description"),
        ("wagtaildocs", "0014_alter_document_file_size"),
        ("wagtail_localize", "0016_rename_page_revision_translationlog_revision"),
        ("orion_localization", "0001_initial"),
        ("orion_site_data", "0003_site_location"),
        ("orion_navigation", "0002_grant_menus_to_editors"),
        ("orion_pages", "0004_add_map_block"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
