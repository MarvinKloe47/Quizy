"""Helpers for setting and clearing authentication cookies."""

from django.conf import settings
from rest_framework_simplejwt.settings import api_settings


def set_token_cookies(response, access_token, refresh_token):
    """Attach access and refresh JWT cookies to the response."""
    set_access_cookie(response, access_token)
    set_refresh_cookie(response, refresh_token)


def set_access_cookie(response, access_token):
    """Attach the access token cookie to the response."""
    max_age = int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
    set_cookie(response, "access_token", str(access_token), max_age)


def set_refresh_cookie(response, refresh_token):
    """Attach the refresh token cookie to the response."""
    max_age = int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
    set_cookie(response, "refresh_token", str(refresh_token), max_age)


def set_cookie(response, name, value, max_age):
    """Set one secure, HTTP-only auth cookie."""
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
    )


def clear_token_cookies(response):
    """Remove both authentication cookies from the browser."""
    delete_cookie(response, "access_token")
    delete_cookie(response, "refresh_token")


def delete_cookie(response, name):
    """Delete one authentication cookie using the configured path."""
    response.delete_cookie(
        name,
        path=settings.AUTH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
