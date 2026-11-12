import hashlib
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

TOKEN_PREFIX = "orion_mcp_"  # noqa: S105 - the start of a token, not a password
TOKEN_RANDOM_LENGTH = 48
SHOWN_PREFIX_LENGTH = 8


def hash_token(token):
    """The SHA-256 of a token. Enough for a random value of high entropy."""
    return hashlib.sha256(token.encode()).hexdigest()


class Scope(models.TextChoices):
    READ_ONLY = "read-only", _("Read only")
    DRAFT_ONLY = "draft-only", _("Read and save drafts")
    FULL = "full", _("Read, save drafts and change redirects and site data")


class ApiKey(models.Model):
    """A key that lets a remote client use the site's MCP endpoint as one user.

    Only the hash of the token is stored; the token itself is shown once, when the key
    is created.
    """

    name = models.CharField(_("name"), max_length=100)
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    prefix = models.CharField(_("key"), max_length=24, editable=False)
    scope = models.CharField(_("scope"), max_length=12, choices=Scope.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("acts as"),
        on_delete=models.CASCADE,
        related_name="+",
    )
    expires_at = models.DateTimeField(_("expires"), null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    last_used_at = models.DateTimeField(_("last used"), null=True, blank=True)
    revoked_at = models.DateTimeField(_("revoked"), null=True, blank=True)

    class Meta:
        verbose_name = _("API key")
        verbose_name_plural = _("API keys")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.prefix}…)"

    @staticmethod
    def check_user(user):
        """A key acts as an active account that is not a superuser."""
        if not user.is_active:
            raise ValidationError(_("The user is not active."))
        if user.is_superuser:
            raise ValidationError(
                _("A key cannot act as a superuser: it would skip every permission.")
            )

    def clean(self):
        super().clean()
        if self.user_id:
            self.check_user(self.user)

    @classmethod
    def issue(cls, *, name, scope, user, created_by=None, expires_at=None):
        """Create a key and return it with its token, which cannot be read again."""
        cls.check_user(user)
        token = (
            TOKEN_PREFIX
            + secrets.token_urlsafe(TOKEN_RANDOM_LENGTH)[:TOKEN_RANDOM_LENGTH]
        )
        key = cls.objects.create(
            name=name,
            scope=scope,
            user=user,
            created_by=created_by,
            expires_at=expires_at,
            key_hash=hash_token(token),
            prefix=token[: len(TOKEN_PREFIX) + SHOWN_PREFIX_LENGTH],
        )
        return key, token

    @property
    def status(self):
        if self.revoked_at is not None:
            return "revoked"
        if self.expires_at is not None and self.expires_at <= timezone.now():
            return "expired"
        return "active"

    def revoke(self):
        if self.revoked_at is None:
            self.revoked_at = timezone.now()
            self.save(update_fields=["revoked_at"])


class OperationReceipt(models.Model):
    """The result of a write a key already made, so that a retry does not repeat it."""

    key = models.ForeignKey(ApiKey, on_delete=models.CASCADE, related_name="receipts")
    tool = models.CharField(max_length=64)
    operation_key = models.CharField(max_length=100)
    payload_hash = models.CharField(max_length=64)
    result = models.JSONField()
    # What a settings write changed, to undo it: the target, the values it replaced
    # and the values it wrote. Empty for the writes that cannot be undone.
    before = models.JSONField(null=True, blank=True)
    reverted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "tool", "operation_key"],
                name="orion_mcp_one_receipt_per_operation",
            )
        ]

    def __str__(self):
        return f"{self.tool} {self.operation_key}"
