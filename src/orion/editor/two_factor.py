"""The admin's second factor: an authenticator app (TOTP) and single-use backup codes.

TwoFactorMiddleware sends unverified admin users here: to "verify" when they have a
confirmed authenticator, or to "setup" when they do not.
"""

from base64 import b32encode

import segno
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django_otp import devices_for_user, match_token, user_has_device
from django_otp import login as otp_login
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from orion.editor.roles import is_site_administrator

BACKUP_CODE_COUNT = 10
SESSION_BACKUP_CODES = "orion_2fa_backup_codes"


class CodeForm(forms.Form):
    code = forms.CharField(
        label=_("Code"),
        max_length=16,
        widget=forms.TextInput(
            attrs={"autocomplete": "one-time-code", "autofocus": True}
        ),
    )

    def clean_code(self):
        return "".join(self.cleaned_data["code"].split()).lower()


def _next_url(request):
    url = request.POST.get("next") or request.GET.get("next")
    if url and url_has_allowed_host_and_scheme(
        url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return url
    return reverse("wagtailadmin_home")


def _new_backup_codes(user):
    """Replace the user's backup codes with new ones and return them."""
    StaticDevice.objects.filter(user=user).delete()
    device = StaticDevice.objects.create(user=user, name="backup")
    codes = [StaticToken.random_token() for _number in range(BACKUP_CODE_COUNT)]
    StaticToken.objects.bulk_create(
        StaticToken(device=device, token=code) for code in codes
    )
    return codes


def _remove_devices(user):
    for device in devices_for_user(user, confirmed=None):
        device.delete()


@require_http_methods(["GET", "POST"])
def verify(request):
    """Ask for a code from the authenticator app or a backup code."""
    if request.user.is_verified():
        return redirect(_next_url(request))
    if not user_has_device(request.user):
        return redirect(f"{reverse('orion_2fa_setup')}?{request.GET.urlencode()}")
    form = CodeForm(request.POST or None)
    if form.is_valid():
        device = match_token(request.user, form.cleaned_data["code"])
        if device is not None:
            otp_login(request, device)
            return redirect(_next_url(request))
        form.add_error(
            "code",
            _(
                "The code is not valid or has expired. After several wrong codes, "
                "wait a moment before trying again."
            ),
        )
    return TemplateResponse(
        request,
        "orion/editor/two_factor/verify.html",
        {"form": form, "next": _next_url(request)},
    )


@require_http_methods(["GET", "POST"])
def setup(request):
    """Pair an authenticator app with a QR code, then hand out backup codes."""
    user = request.user
    if user_has_device(user):
        # A paired authenticator is replaced from "My two-factor", once verified.
        return redirect(f"{reverse('orion_2fa_verify')}?{request.GET.urlencode()}")
    device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
    if device is None:
        device = TOTPDevice.objects.create(
            user=user, name="authenticator", confirmed=False
        )
    form = CodeForm(request.POST or None)
    if form.is_valid():
        if device.verify_token(form.cleaned_data["code"]):
            device.confirmed = True
            device.save()
            otp_login(request, device)
            request.session[SESSION_BACKUP_CODES] = _new_backup_codes(user)
            return redirect(
                f"{reverse('orion_2fa_backup_codes')}?{request.GET.urlencode()}"
            )
        form.add_error("code", _("The code is not valid. Check the time on the phone."))
    # Apps take the key in base32, as in the QR code; django-otp stores it in hex.
    secret = b32encode(device.bin_key).decode().rstrip("=")
    qr_code = segno.make(device.config_url, error="m").svg_inline(
        scale=5, border=2, title=_("QR code for the authenticator app")
    )
    return TemplateResponse(
        request,
        "orion/editor/two_factor/setup.html",
        {
            "form": form,
            "next": _next_url(request),
            # segno builds this SVG from the device's own provisioning URL.
            "qr_code": mark_safe(qr_code),  # noqa: S308
            "secret": " ".join(secret[i : i + 4] for i in range(0, len(secret), 4)),
        },
    )


def backup_codes(request):
    """Show new backup codes once."""
    codes = request.session.pop(SESSION_BACKUP_CODES, None)
    if not codes:
        return redirect("orion_2fa_manage")
    return TemplateResponse(
        request,
        "orion/editor/two_factor/backup_codes.html",
        {"codes": codes, "next": _next_url(request)},
    )


@require_http_methods(["GET", "POST"])
def manage(request):
    """The user's own second factor: status, new backup codes or a new phone."""
    user = request.user
    if request.method == "POST":
        if request.POST.get("action") == "regenerate":
            request.session[SESSION_BACKUP_CODES] = _new_backup_codes(user)
            return redirect("orion_2fa_backup_codes")
        if request.POST.get("action") == "replace":
            _remove_devices(user)
            return redirect("orion_2fa_setup")
    backup_device = StaticDevice.objects.filter(user=user).first()
    return TemplateResponse(
        request,
        "orion/editor/two_factor/manage.html",
        {
            "has_authenticator": TOTPDevice.objects.filter(
                user=user, confirmed=True
            ).exists(),
            "backup_codes_left": backup_device.token_set.count()
            if backup_device
            else 0,
        },
    )


def can_reset(user, target):
    """Administrators reset others' second factor; only superusers a superuser's."""
    if user.pk == target.pk or not is_site_administrator(user):
        return False
    return user.is_superuser or not target.is_superuser


@require_http_methods(["GET", "POST"])
def reset(request, user_id):
    """Remove another user's second factor so they set it up again."""
    target = get_object_or_404(get_user_model(), pk=user_id)
    if not can_reset(request.user, target):
        raise PermissionDenied
    if request.method == "POST":
        _remove_devices(target)
        messages.success(
            request,
            _("%(user)s will set up the two-factor authentication again at next login.")
            % {"user": target.get_full_name() or target.get_username()},
        )
        return redirect("wagtailusers_users:index")
    return TemplateResponse(
        request, "orion/editor/two_factor/reset.html", {"target": target}
    )
