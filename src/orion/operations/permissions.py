from django.core.exceptions import PermissionDenied


def require_actor(user):
    """Only an authenticated, active user can operate."""
    if user is None or not user.is_authenticated or not user.is_active:
        raise PermissionDenied("The acting user must be an active account.")
    return user


def require_perm(user, permission, action):
    """Fail with a message that says what was not allowed, never changing anything."""
    require_actor(user)
    if not user.has_perm(permission):
        raise PermissionDenied(f"You do not have permission to {action}.")
