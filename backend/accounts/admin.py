"""Admin customizations for user management."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class QuizlyUserAdmin(UserAdmin):
    """Expose useful user fields for Quizly administration."""

    list_display = ("id", "username", "email", "is_staff", "date_joined")
    search_fields = ("username", "email")
