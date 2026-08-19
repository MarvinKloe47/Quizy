"""Tests for quiz APIs and generation services."""

from unittest.mock import patch
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from quizzes.exceptions import QuizGenerationError
from quizzes.models import Quiz
from quizzes.services import generate_quiz_for_user
from quizzes.validators import validate_quiz_payload, validate_youtube_url

User = get_user_model()


class QuizApiTests(TestCase):
    """Cover quiz API behavior and ownership."""

    def setUp(self):
        """Create authenticated and foreign users."""
        self.client = APIClient()
        self.user = create_user("owner")
        self.other = create_user("other")
        self.client.force_authenticate(user=self.user)

    def test_protected_endpoint_requires_auth(self):
        """Unauthenticated quiz list requests are rejected."""
        client = APIClient()
        response = client.get("/api/quizzes/")
        self.assertEqual(response.status_code, 401)

    def test_user_receives_only_own_quizzes(self):
        """The quiz list excludes quizzes owned by other users."""
        quiz = create_quiz(self.user, "Mine")
        create_quiz(self.other, "Other")
        response = self.client.get("/api/quizzes/")
        self.assertEqual([item["id"] for item in response.data], [quiz.id])

    def test_foreign_quiz_access_is_blocked(self):
        """Users cannot read quizzes they do not own."""
        quiz = create_quiz(self.other, "Other")
        response = self.client.get(f"/api/quizzes/{quiz.id}/")
        self.assertEqual(response.status_code, 404)

    def test_patch_own_quiz(self):
        """Users can update their own quiz title and description."""
        quiz = create_quiz(self.user, "Old")
        response = self.client.patch(patch_url(quiz), patch_payload(), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "New")

    def test_delete_own_quiz(self):
        """Users can delete their own quizzes with questions."""
        quiz = create_quiz(self.user, "Delete")
        response = self.client.delete(patch_url(quiz))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Quiz.objects.filter(id=quiz.id).exists())

    @patch("quizzes.views.generate_quiz_for_user")
    def test_quiz_generation_with_mocked_services(self, generator):
        """POST quizzes returns a generated quiz without real AI calls."""
        generator.return_value = create_quiz(self.user, "Generated")
        response = self.client.post("/api/quizzes/", url_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Generated")

    @patch("quizzes.views.generate_quiz_for_user")
    def test_generation_error_leaves_no_half_quiz(self, generator):
        """Generation errors do not persist partial quizzes."""
        generator.side_effect = QuizGenerationError("Boom")
        response = self.client.post("/api/quizzes/", url_payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Quiz.objects.count(), 0)

    @patch("quizzes.services.gemini_service.generate_quiz")
    @patch("quizzes.services.whisper_service.transcribe_audio")
    @patch("quizzes.services.youtube.download_audio")
    def test_pipeline_persists_mocked_external_result(self, audio, whisper, gemini):
        """The service pipeline stores a fully validated generated quiz."""
        audio.return_value = Path("audio.mp3")
        whisper.return_value = "Transcript"
        gemini.return_value = valid_payload()
        quiz = generate_quiz_for_user(self.user, long_url())
        self.assertEqual(quiz.questions.count(), 10)

    @patch("quizzes.services.youtube.download_audio")
    def test_download_error_leaves_no_half_quiz(self, audio):
        """Download failures do not persist a quiz."""
        audio.side_effect = QuizGenerationError("Download failed")
        with self.assertRaises(QuizGenerationError):
            generate_quiz_for_user(self.user, long_url())
        self.assertEqual(Quiz.objects.count(), 0)

    @patch("quizzes.services.whisper_service.transcribe_audio")
    @patch("quizzes.services.youtube.download_audio")
    def test_whisper_error_leaves_no_half_quiz(self, audio, whisper):
        """Whisper failures do not persist a quiz."""
        audio.return_value = Path("audio.mp3")
        whisper.side_effect = QuizGenerationError("Whisper failed")
        with self.assertRaises(QuizGenerationError):
            generate_quiz_for_user(self.user, long_url())
        self.assertEqual(Quiz.objects.count(), 0)

    @patch("quizzes.services.gemini_service.generate_quiz")
    @patch("quizzes.services.whisper_service.transcribe_audio")
    @patch("quizzes.services.youtube.download_audio")
    def test_gemini_error_leaves_no_half_quiz(self, audio, whisper, gemini):
        """Gemini failures do not persist a quiz."""
        audio.return_value = Path("audio.mp3")
        whisper.return_value = "Transcript"
        gemini.side_effect = QuizGenerationError("Gemini failed")
        with self.assertRaises(QuizGenerationError):
            generate_quiz_for_user(self.user, long_url())
        self.assertEqual(Quiz.objects.count(), 0)


class QuizValidationTests(TestCase):
    """Cover YouTube and generated payload validation."""

    def test_youtube_url_validation_accepts_real_urls(self):
        """Validator accepts standard YouTube URL formats."""
        self.assertIn("youtube.com", validate_youtube_url(long_url()))
        self.assertIn("youtu.be", validate_youtube_url(short_url()))

    def test_youtube_url_validation_rejects_other_hosts(self):
        """Validator rejects non-YouTube URLs."""
        with self.assertRaises(QuizGenerationError):
            validate_youtube_url("https://example.com/watch?v=abc")

    def test_payload_requires_ten_questions(self):
        """Generated quiz validation requires exactly ten questions."""
        payload = valid_payload()
        self.assertEqual(len(validate_quiz_payload(payload)["questions"]), 10)
        payload["questions"].pop()
        with self.assertRaises(QuizGenerationError):
            validate_quiz_payload(payload)

    def test_payload_requires_four_options_and_valid_answer(self):
        """Each question must have four options containing the answer."""
        payload = valid_payload()
        payload["questions"][0]["question_options"] = ["A", "B", "C"]
        with self.assertRaises(QuizGenerationError):
            validate_quiz_payload(payload)


def create_user(username):
    """Create a user for quiz tests."""
    return User.objects.create_user(username=username, password="Validpass1")


def create_quiz(user, title):
    """Create a quiz with one question."""
    quiz = Quiz.objects.create(owner=user, title=title, video_url=long_url())
    quiz.questions.create(**question_payload())
    return quiz


def question_payload():
    """Return one valid question payload."""
    return {
        "question_title": "Question?",
        "question_options": ["A", "B", "C", "D"],
        "answer": "A",
    }


def valid_payload():
    """Return one valid generated quiz payload."""
    return {
        "title": "Quiz",
        "description": "Description",
        "questions": [question_payload() for _ in range(10)],
    }


def patch_url(quiz):
    """Return a detail URL for a quiz."""
    return f"/api/quizzes/{quiz.id}/"


def patch_payload():
    """Return an update payload."""
    return {"title": "New", "description": "Changed"}


def url_payload():
    """Return a quiz creation payload."""
    return {"url": long_url()}


def long_url():
    """Return a standard YouTube watch URL."""
    return "https://www.youtube.com/watch?v=abc123xyz"


def short_url():
    """Return a short YouTube URL."""
    return "https://youtu.be/abc123xyz"
