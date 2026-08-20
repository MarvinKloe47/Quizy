"""Application configuration for authentication features."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Register the accounts application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
