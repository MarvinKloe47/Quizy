"""Admin setup for quiz management."""

from django.contrib import admin

from quizzes.models import Question, Quiz, QuizProgress


class QuestionInline(admin.TabularInline):
    """Edit questions directly on a quiz."""

    model = Question
    extra = 0
    fields = ("question_title", "question_options", "answer")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for quizzes."""

    inlines = (QuestionInline,)
    list_display = ("id", "title", "owner", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "description", "video_url", "owner__username")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for quiz questions."""

    list_display = ("id", "quiz", "question_title", "answer")
    search_fields = ("question_title", "answer", "quiz__title")


@admin.register(QuizProgress)
class QuizProgressAdmin(admin.ModelAdmin):
    """Admin configuration for saved quiz progress."""

    list_display = ("id", "user", "quiz", "current_question", "updated_at")
    search_fields = ("user__username", "quiz__title")
