# Quizly Backend

Dieses Repository enthaelt die Django-Backend-Abgabe fuer Quizly.

Das Backend liegt in `backend/` und stellt Authentifizierung, Quizverwaltung
und eine YouTube-zu-Quiz-Pipeline bereit:

YouTube URL -> `yt_dlp` -> FFmpeg -> Whisper -> Gemini -> Django REST API.

Setup, Konfiguration und API-Hinweise stehen in [backend/README.md](backend/README.md).
