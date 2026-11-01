from django.db import models
from django.utils.translation import gettext_lazy as _


class NoResultsQuery(models.Model):
    """A search of the site that found nothing, and how often."""

    query_string = models.CharField(_("search"), max_length=255, unique=True)
    hits = models.PositiveIntegerField(_("searches"), default=1)
    last_seen = models.DateTimeField(_("last search"), auto_now=True)

    class Meta:
        verbose_name = _("search without results")
        verbose_name_plural = _("searches without results")

    def __str__(self):
        return self.query_string
