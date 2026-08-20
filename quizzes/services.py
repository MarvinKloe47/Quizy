"""Application services for quiz creation and progress persistence."""

from tempfile import TemporaryDirectory

from django.db import transaction

from quizzes import gemini_service, whisper_service, youtube
from quizzes.models import Question, Quiz, QuizProgress


def generate_quiz_for_user(user, video_url):
    """Run the complete generation pipeline and persist the result."""
    with TemporaryDirectory() as temp_name:
        transcript = transcribe_video(video_url, temp_name)
        payload = gemini_service.generate_quiz(transcript)
    return save_quiz(user, video_url, payload)


def transcribe_video(video_url, temp_name):
    """Download a video's audio and transcribe it."""
    from pathlib import Path

    audio_path = youtube.download_audio(video_url, Path(temp_name))
    return whisper_service.transcribe_audio(audio_path)


@transaction.atomic
def save_quiz(user, video_url, payload):
    """Save a validated quiz and all questions atomically."""
    quiz = Quiz.objects.create(
        owner=user,
        title=payload["title"],
        description=payload["description"],
        video_url=video_url,
    )
    create_questions(quiz, payload["questions"])
    return quiz


def create_questions(quiz, questions):
    """Create all questions for a quiz."""
    Question.objects.bulk_create([build_question(quiz, item) for item in questions])


def build_question(quiz, item):
    """Build one unsaved question model."""
    return Question(
        quiz=quiz,
        question_title=item["question_title"],
        question_options=item["question_options"],
        answer=item["answer"],
    )


def save_progress(user, quiz, attrs):
    """Create or update saved quiz progress."""
    progress, _ = QuizProgress.objects.update_or_create(
        user=user,
        quiz=quiz,
        defaults=attrs,
    )
    return progress
