"""Application configuration for Quizly quiz features."""

from django.apps import AppConfig


class QuizzesConfig(AppConfig):
    """Register the quizzes application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "quizzes"
