# Quizly Backend Implementation Report

## Architektur

- Django-Projekt unter `backend/config`
- App `accounts` für Registrierung, Login, Refresh, Logout und Cookie-JWT-Authentifizierung
- App `quizzes` für Quizze, Fragen, Fortschritt, Admin, API und externe Services
- Service-Schicht für YouTube-Download, lokale Whisper-Transkription und Gemini-Quizgenerierung

## Endpoints

- `POST /api/register/`
- `POST /api/login/`
- `POST /api/token/refresh/`
- `POST /api/logout/`
- `GET /api/quizzes/`
- `POST /api/quizzes/`
- `GET /api/quizzes/{id}/`
- `PATCH /api/quizzes/{id}/`
- `DELETE /api/quizzes/{id}/`
- `GET/PATCH /api/quizzes/{id}/progress/`

## Models

- `Quiz`: Owner, Titel, Beschreibung, YouTube-URL, Zeitstempel
- `Question`: Quiz-FK, Fragetext, vier Optionen als JSON, korrekte Antwort
- `QuizProgress`: User, Quiz, gespeicherte Antworten, aktuelle Frage

## Auth-Flow

Login erzeugt SimpleJWT Access- und Refresh-Tokens und setzt sie als HTTP-only Cookies. Geschützte DRF-Views lesen den Access-Token aus dem Cookie. Refresh liest den Refresh-Cookie und setzt einen neuen Access-Cookie. Logout blacklisted den Refresh-Token und löscht beide Cookies.

## AI-Pipeline

`POST /api/quizzes/` validiert YouTube-URLs, lädt Audio per `yt_dlp`, verlangt globales FFmpeg, transkribiert per lokalem Whisper und erzeugt mit Gemini Flash strikt validiertes JSON. Persistierung erfolgt erst nach vollständiger Validierung und atomar.

## Tests

Automatisierte Tests decken Registrierung, Login, Cookies, Refresh, Logout, geschützte Endpunkte, Ownership, PATCH, DELETE, YouTube-Validierung, gemockte Quizgenerierung und Fehlerfälle für Download, Whisper und Gemini ab.

## Frontend

Die bestehenden Frontend-Endpunkte und Response-Felder bleiben kompatibel. Für automatische Fortschrittsspeicherung steht zusätzlich `/api/quizzes/{id}/progress/` bereit; das gelieferte Frontend speichert Antworten weiterhin clientseitig und wurde nicht verändert.

## Externe Voraussetzungen

- FFmpeg muss global installiert sein.
- Für echte Quizgenerierung werden `yt_dlp`, `openai-whisper`, `google-genai` und ein gültiger `GEMINI_API_KEY` benötigt.
- Tests mocken externe Dienste und benötigen keine echten YouTube-, Whisper- oder Gemini-Aufrufe.

## Definition of Done

- [x] Django + DRF Backend
- [x] JWT mit HTTP-only Cookies
- [x] Register/Login/Refresh/Logout
- [x] Quiz- und Question-Modelle
- [x] Ownership-Schutz
- [x] YouTube-only URL-Validierung
- [x] yt_dlp/FFmpeg/Whisper/Gemini Service-Schicht
- [x] Atomare Speicherung nach vollständiger Validierung
- [x] Admin für User, Quizze, Fragen und Fortschritt
- [x] Automatisierte Tests mit Mocks
- [x] `.env.example` ohne Secrets
- [x] README mit Setup und Betriebshinweisen
