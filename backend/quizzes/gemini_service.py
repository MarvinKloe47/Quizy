"""Gemini quiz generation helpers."""

import json

from django.conf import settings

from quizzes.exceptions import QuizGenerationError
from quizzes.validators import validate_quiz_payload


def generate_quiz(transcript):
    """Generate and validate a quiz from a transcript."""
    response_text = request_quiz(transcript)
    return validate_quiz_payload(parse_json(response_text))


def request_quiz(transcript):
    """Call Gemini with a strict JSON prompt."""
    ensure_api_key()
    try:
        from google import genai
    except ImportError as exc:
        raise QuizGenerationError("google-genai is not installed.") from exc
    return call_gemini(genai.Client(api_key=settings.GEMINI_API_KEY), transcript)


def ensure_api_key():
    """Ensure Gemini credentials are configured."""
    if not settings.GEMINI_API_KEY:
        raise QuizGenerationError("GEMINI_API_KEY is not configured.")


def call_gemini(client, transcript):
    """Call the configured Gemini model and return text."""
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=build_prompt(transcript),
        config={"response_mime_type": "application/json"},
    )
    return response.text


def build_prompt(transcript):
    """Build a concise prompt for strict quiz JSON."""
    return (
        "Create JSON with title, description and exactly 10 questions. "
        "Each question needs question_title, question_options with 4 strings, "
        "and answer equal to one option. Transcript:\n"
        f"{transcript}"
    )


def parse_json(response_text):
    """Parse Gemini JSON output."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise QuizGenerationError("Gemini returned invalid JSON.") from exc
