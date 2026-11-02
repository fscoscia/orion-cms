from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse
from django.utils.crypto import constant_time_compare, salted_hmac
from django_otp import user_has_device
from django_otp.middleware import OTPMiddleware

# Admin URLs that stay open before the second factor is verified.
UNVERIFIED_URL_NAMES = {
    "wagtailadmin_login",
    "wagtailadmin_logout",
    "wagtailadmin_javascript_catalog",
    "wagtailadmin_sprite",
    "orion_admin_colors",
    "orion_2fa_verify",
    "orion_2fa_setup",
    "orion_2fa_backup_codes",
}


def has_admin_access(user):
    return user.is_authenticated and (
        user.is_superuser or user.has_perm("wagtailadmin.access_admin")
    )


class TwoFactorMiddleware(OTPMiddleware):
    """Requires a verified second factor for every admin page (ORION_2FA_REQUIRED).

    Goes after AuthenticationMiddleware. The public site is left alone.
    """

    async_capable = False

    def __call__(self, request):
        self._install_lazy_accessors(request)
        if self._needs_second_factor(request):
            name = (
                "orion_2fa_verify"
                if user_has_device(request.user)
                else "orion_2fa_setup"
            )
            return redirect(
                f"{reverse(name)}?{urlencode({'next': request.get_full_path()})}"
            )
        return self.get_response(request)

    @staticmethod
    def _needs_second_factor(request):
        if not getattr(settings, "ORION_2FA_REQUIRED", True):
            return False
        if not request.path.startswith(f"/{settings.ORION_ADMIN_PATH}"):
            return False
        user = request.user
        if not has_admin_access(user) or user.is_verified():
            return False
        try:
            return resolve(request.path_info).url_name not in UNVERIFIED_URL_NAMES
        except Resolver404:
            return False


EMAIL_HASH_SESSION_KEY = "orion_email_hash"


def get_email_hash(user):
    return salted_hmac("orion.editor.session_email", user.email or "").hexdigest()


class CredentialsSessionMiddleware:
    """Signs out a user's other sessions when their email changes.

    Django already does it for the password: the session keeps a hash of it. This adds
    one of the email. The session that changes its own user's email keeps working.
    Goes after AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if not user.is_authenticated:
            return self.get_response(request)
        current = get_email_hash(user)
        stored = request.session.get(EMAIL_HASH_SESSION_KEY)
        if stored is None:
            # A session from before this check: adopt it instead of signing it out.
            request.session[EMAIL_HASH_SESSION_KEY] = current
        elif not constant_time_compare(stored, current):
            logout(request)
            return self.get_response(request)
        response = self.get_response(request)
        if (
            request.method == "POST"
            and request.user.is_authenticated
            and request.user.pk == user.pk
        ):
            # The user may have changed their own email in this request.
            user.refresh_from_db(fields=["email"])
            new = get_email_hash(user)
            if new != current:
                request.session[EMAIL_HASH_SESSION_KEY] = new
        return response
