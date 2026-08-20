"""Cookie based JWT authentication for DRF."""

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from accounts.tokens import token_matches_user


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate users from the access token cookie."""

    def authenticate(self, request):
        """Return the authenticated user for the access cookie."""
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        validate_token_version(user, validated_token)
        return user, validated_token


def validate_token_version(user, token):
    """Reject access tokens revoked by logout."""
    if not token_matches_user(user, token):
        raise AuthenticationFailed("Token has been revoked.")
