"""Local Whisper transcription helpers."""

from django.conf import settings

from quizzes.exceptions import QuizGenerationError

_MODEL = None


def transcribe_audio(audio_path):
    """Transcribe an audio file with local Whisper."""
    model = get_model()
    result = model.transcribe(str(audio_path))
    return validate_transcript(result.get("text", ""))


def get_model():
    """Load and cache the configured Whisper model."""
    global _MODEL
    if _MODEL is None:
        _MODEL = load_model()
    return _MODEL


def load_model():
    """Load Whisper using the configured model name."""
    try:
        import whisper
    except ImportError as exc:
        raise QuizGenerationError("Whisper is not installed.") from exc
    return whisper.load_model(settings.WHISPER_MODEL)


def validate_transcript(text):
    """Return a non-empty transcript or raise a domain error."""
    transcript = (text or "").strip()
    if not transcript:
        raise QuizGenerationError("Whisper returned an empty transcript.")
    return transcript
