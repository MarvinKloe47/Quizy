"""Serializers for quizzes, questions and progress."""

from rest_framework import serializers

from quizzes.models import Question, Quiz, QuizProgress


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize one quiz question."""

    class Meta:
        """Question response fields."""

        model = Question
        fields = (
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        )


class QuizSerializer(serializers.ModelSerializer):
    """Serialize quizzes with nested questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        """Quiz response fields."""

        model = Quiz
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        )
        read_only_fields = ("video_url", "questions")


class QuizCreateSerializer(serializers.Serializer):
    """Validate quiz creation requests."""

    url = serializers.URLField()


class QuizProgressSerializer(serializers.ModelSerializer):
    """Serialize saved quiz progress."""

    class Meta:
        """Progress request and response fields."""

        model = QuizProgress
        fields = ("answers", "current_question", "updated_at")
        read_only_fields = ("updated_at",)
