"""Tests for quiz APIs and generation services."""

from unittest.mock import patch
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from quizzes import gemini_service
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

    def test_foreign_quiz_write_and_delete_are_blocked(self):
        """Users cannot update or delete quizzes they do not own."""
        quiz = create_quiz(self.other, "Other")
        patch = self.client.patch(patch_url(quiz), patch_payload(), format="json")
        delete = self.client.delete(patch_url(quiz))
        self.assertEqual(patch.status_code, 404)
        self.assertEqual(delete.status_code, 404)

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

    def test_progress_saves_valid_answers(self):
        """Users can save valid progress for their own quiz."""
        quiz = create_quiz(self.user, "Progress")
        question = quiz.questions.first()
        response = self.client.patch(
            progress_url(quiz),
            progress_payload(question),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["answers"][str(question.id)], "A")

    def test_progress_rejects_foreign_quiz(self):
        """Users cannot read or modify another user's progress."""
        quiz = create_quiz(self.other, "Foreign")
        response = self.client.patch(
            progress_url(quiz),
            {"answers": {}},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_progress_rejects_unknown_question_id(self):
        """Progress rejects answers for questions outside the quiz."""
        quiz = create_quiz(self.user, "Progress")
        response = self.client.patch(
            progress_url(quiz),
            invalid_question_payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_progress_rejects_invalid_answer_option(self):
        """Progress rejects answers not present in the question options."""
        quiz = create_quiz(self.user, "Progress")
        question = quiz.questions.first()
        response = self.client.patch(
            progress_url(quiz),
            progress_payload(question, "Z"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_progress_rejects_current_question_out_of_range(self):
        """Progress rejects impossible current question indexes."""
        quiz = create_quiz(self.user, "Progress")
        question = quiz.questions.first()
        payload = progress_payload(question)
        payload["current_question"] = 99
        response = self.client.patch(progress_url(quiz), payload, format="json")
        self.assertEqual(response.status_code, 400)

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

    def test_youtube_url_validation_rejects_manipulated_urls(self):
        """Validator rejects spoofed, local and file URLs."""
        for url in invalid_urls():
            with self.assertRaises(QuizGenerationError):
                validate_youtube_url(url)

    def test_payload_requires_ten_questions(self):
        """Generated quiz validation requires exactly ten questions."""
        payload = valid_payload()
        self.assertEqual(len(validate_quiz_payload(payload)["questions"]), 10)
        payload["questions"].pop()
        with self.assertRaises(QuizGenerationError):
            validate_quiz_payload(payload)
        payload["questions"].extend([question_payload(), question_payload()])
        with self.assertRaises(QuizGenerationError):
            validate_quiz_payload(payload)

    def test_payload_requires_four_options_and_valid_answer(self):
        """Each question must have four options containing the answer."""
        payload = valid_payload()
        payload["questions"][0]["question_options"] = ["A", "B", "C"]
        with self.assertRaises(QuizGenerationError):
            validate_quiz_payload(payload)

    def test_payload_rejects_empty_and_unexpected_fields(self):
        """Generated quiz validation rejects empty text and extra data."""
        assert_invalid_payload({"title": ""})
        assert_invalid_payload({"extra": "nope"})
        assert_invalid_question({"question_title": ""})
        assert_invalid_question({"extra": "nope"})

    def test_payload_rejects_duplicate_or_bad_answers(self):
        """Generated quiz validation rejects duplicate options and bad answers."""
        assert_invalid_question({"question_options": ["A", "A", "C", "D"]})
        assert_invalid_question({"answer": ""})
        assert_invalid_question({"answer": "Z"})


class GeminiServiceTests(TestCase):
    """Cover Gemini integration error handling."""

    @override_settings(GEMINI_API_KEY="configured")
    @patch("quizzes.gemini_service.build_client")
    @patch("quizzes.gemini_service.call_gemini")
    def test_sdk_errors_are_domain_errors(self, call, build_client):
        """SDK API failures are mapped to generation errors."""
        from google.genai import errors

        call.side_effect = errors.ClientError(404, {"error": {}}, None)
        with self.assertRaises(QuizGenerationError):
            gemini_service.request_quiz("Transcript")
        build_client.assert_called_once()


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


def progress_url(quiz):
    """Return the progress URL for a quiz."""
    return f"/api/quizzes/{quiz.id}/progress/"


def patch_payload():
    """Return an update payload."""
    return {"title": "New", "description": "Changed"}


def progress_payload(question, answer="A"):
    """Return valid progress data."""
    return {"answers": {str(question.id): answer}, "current_question": 0}


def invalid_question_payload():
    """Return progress with a non-existing question id."""
    return {"answers": {"999999": "A"}, "current_question": 0}


def url_payload():
    """Return a quiz creation payload."""
    return {"url": long_url()}


def long_url():
    """Return a standard YouTube watch URL."""
    return "https://www.youtube.com/watch?v=abc123xyz"


def short_url():
    """Return a short YouTube URL."""
    return "https://youtu.be/abc123xyz"


def invalid_urls():
    """Return URLs that must never be accepted as YouTube videos."""
    return [
        "",
        "not a url",
        "file:///tmp/video.mp4",
        "http://localhost/watch?v=abc",
        "https://youtube.com.example.com/watch?v=abc",
        "https://example.com/?next=youtube.com/watch?v=abc",
    ]


def assert_invalid_payload(overrides):
    """Assert a top-level generated quiz override is invalid."""
    payload = valid_payload()
    payload.update(overrides)
    assert_raises_generation_error(payload)


def assert_invalid_question(overrides):
    """Assert a generated question override is invalid."""
    payload = valid_payload()
    payload["questions"][0].update(overrides)
    assert_raises_generation_error(payload)


def assert_raises_generation_error(payload):
    """Assert a generated quiz payload is rejected."""
    try:
        validate_quiz_payload(payload)
    except QuizGenerationError:
        return
    raise AssertionError("Payload should have been rejected.")
