"""Token-version helpers for JWT issuance and revocation."""

from django.db.models import F
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import UserTokenState


def issue_tokens(user):
    """Issue matching access and refresh tokens for a user."""
    refresh = issue_refresh(user)
    return refresh.access_token, refresh


def issue_refresh(user):
    """Create a refresh token carrying the current token version."""
    refresh = RefreshToken.for_user(user)
    refresh["token_version"] = token_version(user)
    return refresh


def token_version(user):
    """Return the current token version for a user."""
    state, _ = UserTokenState.objects.get_or_create(user=user)
    return state.token_version


def revoke_user_tokens(user):
    """Increment the token version to invalidate existing tokens."""
    UserTokenState.objects.get_or_create(user=user)
    UserTokenState.objects.filter(user=user).update(
        token_version=F("token_version") + 1,
    )


def token_matches_user(user, token):
    """Return whether a token belongs to the user's current version."""
    return token.get("token_version") == token_version(user)


def refresh_from_cookie(request):
    """Return a valid refresh token object from cookies."""
    try:
        return RefreshToken(request.COOKIES.get("refresh_token", ""))
    except TokenError:
        return None
