"""The technical account the server writes as when writing is allowed."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from orion.editor.roles import EDITORS_GROUP

AGENT_USERNAME = "orion-agent"
CREATE_COMMAND = "orion_create_agent_user"


class AgentAccountError(Exception):
    """The account cannot be used to write."""


def find_agent_user():
    user_model = get_user_model()
    return user_model.objects.filter(
        **{user_model.USERNAME_FIELD: AGENT_USERNAME}
    ).first()


def check_agent_user():
    """Return the account to write as, or say why it cannot be used."""
    user = find_agent_user()
    if user is None:
        raise AgentAccountError(
            f"The account {AGENT_USERNAME} does not exist. Create it once with "
            f"`manage.py {CREATE_COMMAND}`."
        )
    if not user.is_active:
        raise AgentAccountError(f"The account {AGENT_USERNAME} is not active.")
    if user.is_superuser:
        raise AgentAccountError(
            f"The account {AGENT_USERNAME} is a superuser, which skips every "
            "permission. Remove that before writing with it."
        )
    return user


def create_agent_user():
    """Create the account if it is missing; return it and whether it was created."""
    user = find_agent_user()
    if user is not None:
        return user, False
    editors = Group.objects.filter(name=EDITORS_GROUP).first()
    if editors is None:
        raise AgentAccountError(
            f"The group {EDITORS_GROUP} does not exist. Run `manage.py migrate` first."
        )
    user_model = get_user_model()
    user = user_model(**{user_model.USERNAME_FIELD: AGENT_USERNAME}, is_active=True)
    user.set_unusable_password()
    user.save()
    user.groups.add(editors)
    return user, True
