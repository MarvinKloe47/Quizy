"""Authentication API views."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.cookies import clear_token_cookies, set_access_cookie
from accounts.cookies import set_token_cookies
from accounts.serializers import LoginSerializer, RegisterSerializer
from accounts.tokens import issue_tokens, refresh_from_cookie
from accounts.tokens import revoke_user_tokens, token_matches_user


class RegisterView(APIView):
    """Create a new user account."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """Register a user and return the documented success body."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(success("User created successfully!"), status=201)


class LoginView(APIView):
    """Authenticate users and issue HTTP-only JWT cookies."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """Log in a user and set access and refresh cookies."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(success("Invalid credentials."), status=401)
        user = serializer.validated_data["user"]
        response = Response(login_payload(user), status=status.HTTP_200_OK)
        set_token_cookies(response, *issue_tokens(user))
        return response


class TokenRefreshView(APIView):
    """Refresh the access token from the refresh cookie."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """Set a new access cookie from a valid refresh token."""
        refresh = refresh_from_cookie(request)
        if not refresh_is_current(refresh):
            return Response(success("Refresh token invalid."), status=401)
        response = Response(success("Token refreshed"), status=200)
        set_access_cookie(response, refresh.access_token)
        return response


class LogoutView(APIView):
    """Blacklist refresh tokens and clear auth cookies."""

    def post(self, request):
        """Log out an authenticated user."""
        blacklist_refresh(request.COOKIES.get("refresh_token"))
        revoke_user_tokens(request.user)
        response = Response(success(logout_detail()), status=200)
        clear_token_cookies(response)
        return response


def success(detail):
    """Build a detail response payload."""
    return {"detail": detail}


def login_payload(user):
    """Build the documented login response body."""
    return {"detail": "Login successfully!", "user": user_payload(user)}


def user_payload(user):
    """Build a public user object."""
    return {"id": user.id, "username": user.username, "email": user.email}


def blacklist_refresh(raw_token):
    """Blacklist a refresh token when present and valid."""
    try:
        if raw_token:
            RefreshToken(raw_token).blacklist()
    except TokenError:
        return


def refresh_is_current(refresh):
    """Return whether the refresh token is valid for its user."""
    if refresh is None:
        return False
    user = refresh_user(refresh)
    return user is not None and token_matches_user(user, refresh)


def refresh_user(refresh):
    """Return the authenticated refresh-token user."""
    from django.contrib.auth import get_user_model

    user_id = refresh.get("user_id")
    return get_user_model().objects.filter(id=user_id).first()


def logout_detail():
    """Return the documented logout message."""
    return (
        "Log-Out successfully! All Tokens will be deleted. "
        "Refresh token is now invalid."
    )
