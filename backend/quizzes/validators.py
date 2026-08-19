"""Validation helpers for YouTube URLs and generated quiz payloads."""

from urllib.parse import parse_qs, urlparse

from quizzes.exceptions import QuizGenerationError

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}


def validate_youtube_url(url):
    """Validate and normalize accepted YouTube URLs."""
    parsed_url = urlparse((url or "").strip())
    if is_watch_url(parsed_url) or is_short_url(parsed_url):
        return parsed_url.geturl()
    raise QuizGenerationError("Only YouTube video URLs are accepted.")


def is_watch_url(parsed_url):
    """Return whether the URL is a youtube.com watch URL."""
    query = parse_qs(parsed_url.query)
    return parsed_url.scheme in schemes() and is_youtube_watch(parsed_url, query)


def is_short_url(parsed_url):
    """Return whether the URL is a youtu.be short URL."""
    return (
        parsed_url.scheme in schemes()
        and parsed_url.netloc == "youtu.be"
        and parsed_url.path.strip("/")
    )


def is_youtube_watch(parsed_url, query):
    """Return whether the parsed URL points to a concrete video."""
    return (
        parsed_url.netloc in YOUTUBE_HOSTS
        and parsed_url.path == "/watch"
        and query.get("v")
    )


def schemes():
    """Return accepted URL schemes."""
    return {"http", "https"}


def validate_quiz_payload(payload):
    """Validate Gemini quiz structure and return it."""
    validate_quiz_fields(payload)
    validate_questions(payload["questions"])
    return payload


def validate_quiz_fields(payload):
    """Ensure top-level quiz fields exist."""
    required = {"title", "description", "questions"}
    if not isinstance(payload, dict) or not required.issubset(payload):
        raise QuizGenerationError("Generated quiz has invalid structure.")


def validate_questions(questions):
    """Ensure the generated quiz has exactly ten valid questions."""
    if not isinstance(questions, list) or len(questions) != 10:
        raise QuizGenerationError("Generated quiz must contain 10 questions.")
    for question in questions:
        validate_question(question)


def validate_question(question):
    """Ensure one question has title, four options, and a valid answer."""
    required = {"question_title", "question_options", "answer"}
    if not isinstance(question, dict) or not required.issubset(question):
        raise QuizGenerationError("Generated question has invalid fields.")
    validate_options(question["question_options"], question["answer"])


def validate_options(options, answer):
    """Ensure options contain exactly four entries and the answer."""
    if not isinstance(options, list) or len(options) != 4:
        raise QuizGenerationError("Each question must contain 4 options.")
    if answer not in options:
        raise QuizGenerationError("The correct answer must be an option.")
