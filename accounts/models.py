"""Account support models."""

from django.conf import settings
from django.db import models


class UserTokenState(models.Model):
    """Track token versions so logout invalidates access tokens."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token_version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return a readable token state label."""
        return f"{self.user} tokens v{self.token_version}"
