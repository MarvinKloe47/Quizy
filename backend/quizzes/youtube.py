"""YouTube audio download helpers."""

import shutil

from quizzes.exceptions import QuizGenerationError
from quizzes.validators import validate_youtube_url


def download_audio(url, target_dir):
    """Download a YouTube video as an audio file into target_dir."""
    safe_url = validate_youtube_url(url)
    ensure_ffmpeg()
    return run_download(safe_url, target_dir)


def ensure_ffmpeg():
    """Ensure FFmpeg is available for yt_dlp post-processing."""
    if shutil.which("ffmpeg") is None:
        raise QuizGenerationError("FFmpeg is required and was not found.")


def run_download(url, target_dir):
    """Run yt_dlp and return the downloaded audio file path."""
    try:
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise QuizGenerationError("yt_dlp is not installed.") from exc
    return execute_download(YoutubeDL, url, target_dir)


def execute_download(youtube_dl, url, target_dir):
    """Execute yt_dlp with audio extraction options."""
    options = download_options(target_dir)
    with youtube_dl(options) as downloader:
        info = downloader.extract_info(url, download=True)
    return resolve_audio_path(info, target_dir)


def download_options(target_dir):
    """Return yt_dlp options for audio extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": str(target_dir / "%(id)s.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        "quiet": True,
        "noplaylist": True,
    }


def resolve_audio_path(info, target_dir):
    """Find the produced audio file path."""
    video_id = info.get("id")
    audio_path = target_dir / f"{video_id}.mp3"
    if audio_path.exists():
        return audio_path
    raise QuizGenerationError("Audio download did not produce a file.")
