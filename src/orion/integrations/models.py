"""The state of the site's external services, as the admin's Integrations show it."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class EmailStatus(models.Model):
    """The last email delivery that worked and the last that failed: a single row.

    It never keeps recipients, contents or credentials.
    """

    last_success_at = models.DateTimeField(_("last email sent at"), null=True)
    last_failure_at = models.DateTimeField(_("last email failed at"), null=True)
    last_error = models.TextField(_("last error"), blank=True)

    class Meta:
        verbose_name = _("email status")
        verbose_name_plural = _("email status")

    def __str__(self):
        return str(self._meta.verbose_name)

    @classmethod
    def load(cls):
        """The status row, or an empty unsaved one before the first delivery."""
        return cls.objects.filter(pk=1).first() or cls(pk=1)

    @property
    def is_failing(self):
        """Whether the last delivery attempt failed."""
        if self.last_failure_at is None:
            return False
        return (
            self.last_success_at is None or self.last_failure_at > self.last_success_at
        )
