"""Quiz API views."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from quizzes.exceptions import QuizGenerationError
from quizzes.models import Quiz
from quizzes.serializers import QuizCreateSerializer, QuizProgressSerializer
from quizzes.serializers import QuizSerializer
from quizzes.services import generate_quiz_for_user, save_progress


class QuizViewSet(viewsets.ModelViewSet):
    """Manage the authenticated user's quizzes."""

    serializer_class = QuizSerializer
    http_method_names = ("get", "post", "patch", "delete")

    def get_queryset(self):
        """Return only quizzes owned by the authenticated user."""
        return Quiz.objects.filter(
            owner=self.request.user,
        ).prefetch_related("questions")

    def create(self, request):
        """Generate a quiz from a YouTube URL."""
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.create_from_url(request, serializer.validated_data["url"])

    def create_from_url(self, request, video_url):
        """Run quiz generation and serialize the created quiz."""
        try:
            quiz = generate_quiz_for_user(request.user, video_url)
        except QuizGenerationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get", "patch"), url_path="progress")
    def progress(self, request, pk=None):
        """Read or save quiz progress for the authenticated user."""
        quiz = self.get_object()
        if request.method == "GET":
            return self.progress_response(request, quiz)
        return self.save_progress_response(request, quiz)

    def progress_response(self, request, quiz):
        """Return saved progress or an empty state."""
        progress = quiz.progress.filter(user=request.user).first()
        serializer = QuizProgressSerializer(
            progress or empty_progress(),
            context={"quiz": quiz},
        )
        return Response(serializer.data, status=200)

    def save_progress_response(self, request, quiz):
        """Validate and persist quiz progress."""
        serializer = QuizProgressSerializer(
            data=request.data,
            context={"quiz": quiz},
        )
        serializer.is_valid(raise_exception=True)
        progress = save_progress(request.user, quiz, serializer.validated_data)
        return Response(progress_payload(progress, quiz), status=200)


def empty_progress():
    """Return an unsaved empty progress object."""
    from quizzes.models import QuizProgress

    return QuizProgress(answers={}, current_question=0)


def progress_payload(progress, quiz):
    """Serialize progress with quiz context."""
    return QuizProgressSerializer(progress, context={"quiz": quiz}).data
