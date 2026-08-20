"""Validation helpers for YouTube URLs and generated quiz payloads."""

from urllib.parse import parse_qs, urlparse

from quizzes.exceptions import QuizGenerationError

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
QUIZ_KEYS = {"title", "description", "questions"}
QUESTION_KEYS = {"question_title", "question_options", "answer"}


def validate_youtube_url(url):
    """Validate and normalize accepted YouTube URLs."""
    parsed_url = urlparse((url or "").strip())
    if is_watch_url(parsed_url) or is_short_url(parsed_url):
        return parsed_url.geturl()
    raise QuizGenerationError("Only YouTube video URLs are accepted.")


def is_watch_url(parsed_url):
    """Return whether the URL is a youtube.com watch URL."""
    query = parse_qs(parsed_url.query)
    return has_allowed_scheme(parsed_url) and is_youtube_watch(parsed_url, query)


def is_short_url(parsed_url):
    """Return whether the URL is a youtu.be short URL."""
    return (
        has_allowed_scheme(parsed_url)
        and parsed_url.hostname == "youtu.be"
        and parsed_url.path.strip("/")
    )


def is_youtube_watch(parsed_url, query):
    """Return whether the parsed URL points to a concrete video."""
    return (
        parsed_url.hostname in YOUTUBE_HOSTS
        and parsed_url.path == "/watch"
        and query.get("v")
    )


def has_allowed_scheme(parsed_url):
    """Return whether the URL uses HTTP or HTTPS."""
    return parsed_url.scheme in {"http", "https"}


def validate_quiz_payload(payload):
    """Validate Gemini quiz structure and return it."""
    validate_quiz_fields(payload)
    validate_questions(payload["questions"])
    return payload


def validate_quiz_fields(payload):
    """Ensure top-level quiz fields exist."""
    if not isinstance(payload, dict) or set(payload) != QUIZ_KEYS:
        raise QuizGenerationError("Generated quiz has invalid structure.")
    validate_text(payload["title"], "Quiz title")
    validate_text(payload["description"], "Quiz description")


def validate_questions(questions):
    """Ensure the generated quiz has exactly ten valid questions."""
    if not isinstance(questions, list) or len(questions) != 10:
        raise QuizGenerationError("Generated quiz must contain 10 questions.")
    for question in questions:
        validate_question(question)


def validate_question(question):
    """Ensure one question has title, four options, and a valid answer."""
    if not isinstance(question, dict) or set(question) != QUESTION_KEYS:
        raise QuizGenerationError("Generated question has invalid fields.")
    validate_text(question["question_title"], "Question title")
    validate_text(question["answer"], "Question answer")
    validate_options(question["question_options"], question["answer"])


def validate_options(options, answer):
    """Ensure options contain exactly four entries and the answer."""
    if not isinstance(options, list) or len(options) != 4:
        raise QuizGenerationError("Each question must contain 4 options.")
    validate_option_texts(options)
    if answer not in options:
        raise QuizGenerationError("The correct answer must be an option.")


def validate_text(value, label):
    """Ensure a generated text value is non-empty."""
    if not isinstance(value, str) or not value.strip():
        raise QuizGenerationError(f"{label} must not be empty.")


def validate_option_texts(options):
    """Ensure options are non-empty and unique strings."""
    for option in options:
        validate_text(option, "Question option")
    if len(set(options)) != len(options):
        raise QuizGenerationError("Question options must be unique.")
