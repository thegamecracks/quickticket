from django.contrib import messages
from django.contrib.auth.models import Group
from django_pyoidc import get_user_by_email
from django_pyoidc.utils import extract_claim_from_tokens


def on_login(request, user):
    messages.success(
        request,
        f"Welcome '{user.username}', you have been logged in",
    )


def on_logout(request, logout_request_args):
    messages.success(
        request,
        f"{request.user.username}, you have been logged out successfully",
    )


def get_user(client, tokens):
    user = get_user_by_email(tokens)
    user.first_name = extract_claim_from_tokens("given_name", tokens)
    user.last_name = extract_claim_from_tokens("family_name", tokens)
    groups = extract_claim_from_tokens("groups", tokens)
    user.is_staff = "admins" in groups

    for group_name in groups:
        group, _ = Group.objects.get_or_create(name=group_name)
        group.user_set.add(user)
        group.save()

    user.save()
    return user
