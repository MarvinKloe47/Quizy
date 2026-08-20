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

    def validate(self, attrs):
        """Validate progress against the current quiz questions."""
        quiz = self.context["quiz"]
        validate_current_question(attrs["current_question"], quiz)
        validate_answers(attrs["answers"], question_map(quiz))
        return attrs


def validate_current_question(current_question, quiz):
    """Ensure the current question index belongs to the quiz."""
    if current_question >= quiz.questions.count():
        raise serializers.ValidationError(
            {"current_question": "Question index is out of range."}
        )


def validate_answers(answers, questions):
    """Ensure all saved answers belong to the quiz and options."""
    if not isinstance(answers, dict):
        raise serializers.ValidationError({"answers": "Answers must be an object."})
    for question_id, answer in answers.items():
        validate_answer(question_id, answer, questions)


def validate_answer(question_id, answer, questions):
    """Validate one saved answer against one quiz question."""
    question = questions.get(str(question_id))
    if question is None:
        raise serializers.ValidationError({"answers": "Unknown question id."})
    if answer not in question.question_options:
        raise serializers.ValidationError({"answers": "Invalid answer option."})


def question_map(quiz):
    """Return quiz questions keyed by their string id."""
    return {str(question.id): question for question in quiz.questions.all()}
