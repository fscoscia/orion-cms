"""Update the site data and the site texts."""

from django.core.exceptions import PermissionDenied, ValidationError
from wagtail.models import Locale

from orion.operations.fields import (
    assign_fields,
    changes,
    snapshot,
    writable_model_fields,
)
from orion.operations.permissions import require_actor, require_perm
from orion.site_data.models import SiteSettings, SiteTexts


def update_site_settings(actor, values):
    require_perm(actor, "orion_site_data.change_sitesettings", "change the site data")
    settings = SiteSettings.load()
    names = [name for name in values if name in writable_model_fields(SiteSettings)]
    before = snapshot(settings, names)
    assign_fields(settings, values, writable_model_fields(SiteSettings))
    settings.full_clean()
    settings.save()
    # What was changed, so that a caller can undo it (see `orion.mcp`).
    settings.change = changes(before, snapshot(settings, names))
    return settings


def update_site_texts(actor, language, values):
    require_actor(actor)
    locale = Locale.objects.filter(language_code=language).first()
    if locale is None:
        raise ValidationError(f"The site has no language {language}.")
    texts = SiteTexts.objects.filter(locale=locale).first()
    permission = "change_sitetexts" if texts else "add_sitetexts"
    if not actor.has_perm(f"orion_site_data.{permission}"):
        raise PermissionDenied("You do not have permission to change the site texts.")
    created = texts is None
    if created:
        texts = SiteTexts(locale=locale)
    allowed = writable_model_fields(SiteTexts, exclude={"locale", "translation_key"})
    names = [name for name in values if name in allowed]
    before = snapshot(texts, names)
    assign_fields(texts, values, allowed)
    texts.full_clean()
    texts.save()
    # A first version of the texts has nothing to go back to.
    texts.change = None if created else changes(before, snapshot(texts, names))
    return texts
