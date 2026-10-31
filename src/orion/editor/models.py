import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def new_token():
    return secrets.token_urlsafe(32)


class PreviewLinkQuerySet(models.QuerySet):
    def active(self):
        return self.filter(expires_at__gt=timezone.now())


class PreviewLink(models.Model):
    """A temporary link that shows a page's latest draft to someone without an
    account. Revoking a link deletes it."""

    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="orion_preview_links",
        verbose_name=_("page"),
    )
    # Kept in clear so the link can be copied again; it only shows drafts and expires.
    token = models.CharField(
        _("token"), max_length=64, unique=True, default=new_token, editable=False
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("created by"),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("expires at"))

    objects = PreviewLinkQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("preview link")
        verbose_name_plural = _("preview links")

    def __str__(self):
        return f"{self.page} ({self.expires_at:%Y-%m-%d})"
