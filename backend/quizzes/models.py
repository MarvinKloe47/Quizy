"""Database models for generated quizzes and quiz progress."""

from django.conf import settings
from django.db import models


class Quiz(models.Model):
    """A quiz generated from one YouTube video."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Order newest quizzes first."""

        ordering = ("-created_at",)

    def __str__(self):
        """Return the title for admin lists."""
        return self.title


class Question(models.Model):
    """One multiple-choice question belonging to a quiz."""

    quiz = models.ForeignKey(
        Quiz,
        related_name="questions",
        on_delete=models.CASCADE,
    )
    question_title = models.CharField(max_length=500)
    question_options = models.JSONField()
    answer = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Keep questions in creation order."""

        ordering = ("id",)

    def __str__(self):
        """Return a readable question label."""
        return self.question_title


class QuizProgress(models.Model):
    """Persist the current answer state for one user's quiz run."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, related_name="progress", on_delete=models.CASCADE)
    answers = models.JSONField(default=dict)
    current_question = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Allow one saved progress entry per user and quiz."""

        unique_together = ("user", "quiz")

    def __str__(self):
        """Return a readable progress label."""
        return f"{self.user} - {self.quiz}"
