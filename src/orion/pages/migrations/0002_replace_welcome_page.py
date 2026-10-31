"""Replace Wagtail's welcome page with an Orion home page on a fresh install.

Only when the default site's root is still Wagtail's untouched welcome page: a plain
page with its original title, no children, no translations and no revisions. In any
other case nothing changes. There is no reverse: the welcome page has no content.
"""

from django.conf import settings
from django.db import migrations
from django.utils import translation
from django.utils.text import slugify
from django.utils.translation import gettext

WELCOME_TITLE = "Welcome to your new Wagtail site!"


def is_untouched_welcome_page(page, page_model, page_content_type_id):
    return (
        page.content_type_id == page_content_type_id
        and page.title == WELCOME_TITLE
        and page.depth == 2
        and page.numchild == 0
        and page.latest_revision_id is None
        and not page_model.objects.filter(translation_key=page.translation_key)
        .exclude(pk=page.pk)
        .exists()
    )


def replace_welcome_page(apps, schema_editor):
    page_model = apps.get_model("wagtailcore", "Page")
    site_model = apps.get_model("wagtailcore", "Site")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    home_page_model = apps.get_model("orion_pages", "HomePage")

    site = site_model.objects.filter(is_default_site=True).first()
    if site is None:
        return
    welcome_page = page_model.objects.filter(pk=site.root_page_id).first()
    page_content_type = content_type_model.objects.filter(
        app_label="wagtailcore", model="page"
    ).first()
    if (
        welcome_page is None
        or page_content_type is None
        or not is_untouched_welcome_page(welcome_page, page_model, page_content_type.pk)
    ):
        return

    tree_path, locale_id = welcome_page.path, welcome_page.locale_id
    # The site's root page is deleted on cascade with it, so point the site at the
    # tree root meanwhile and keep the same site.
    site.root_page_id = page_model.objects.get(depth=1).pk
    site.save(update_fields=["root_page"])
    welcome_page.delete()

    with translation.override(settings.LANGUAGE_CODE):
        title = gettext("Home")
    slug = slugify(title) or "home"
    home_content_type, _created = content_type_model.objects.get_or_create(
        app_label="orion_pages", model="homepage"
    )
    home_page = home_page_model.objects.create(
        title=title,
        draft_title=title,
        slug=slug,
        content_type=home_content_type,
        path=tree_path,
        depth=2,
        numchild=0,
        url_path=f"/{slug}/",
        locale_id=locale_id,
        live=True,
        body=[],
    )
    site.root_page_id = home_page.pk
    site.save(update_fields=["root_page"])
    # Keep the tree consistent whether or not the delete above updated it.
    page_model.objects.filter(depth=1).update(
        numchild=page_model.objects.filter(depth=2).count()
    )


class Migration(migrations.Migration):
    dependencies = [
        ("orion_pages", "0001_initial"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(replace_welcome_page, migrations.RunPython.noop)]
