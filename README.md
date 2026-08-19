# Quizly

Quizly besteht aus einem bereitgestellten Frontend und einem Django-Backend unter `backend/`. Das Backend stellt Authentifizierung per JWT in HTTP-only Cookies bereit und erzeugt Quizze aus YouTube-Videos über `yt_dlp`, FFmpeg, lokales Whisper und Gemini Flash.

## Backend Setup

Empfohlen: Python 3.14.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Trage in `backend/.env` einen gültigen `GEMINI_API_KEY` ein. Für lokale Entwicklung sind die übrigen Defaults auf `http://127.0.0.1:8000` und typische Live-Server-Origins ausgelegt.

## FFmpeg

FFmpeg muss global installiert sein, weil Whisper und die Audio-Extraktion darauf angewiesen sind.

```powershell
winget install --id Gyan.FFmpeg -e --source winget
ffmpeg -version
```

## Datenbank und Server

```powershell
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

## Tests und Checks

```powershell
cd backend
python manage.py check
python manage.py test accounts quizzes
python -m pycodestyle --max-line-length=88 .
```

Die Tests mocken externe Dienste. Für echte Quizgenerierung müssen FFmpeg, `yt_dlp`, `openai-whisper`, `google-genai` und ein Gemini-Key vorhanden sein.

## Frontend Start

Starte `frontend/` mit einem lokalen Webserver, zum Beispiel VS Code Live Server. Das Frontend erwartet:

```js
const API_BASE_URL = "http://127.0.0.1:8000/api/";
```

Falls der Frontend-Port abweicht, ergänze ihn in `CORS_ALLOWED_ORIGINS` und `CSRF_TRUSTED_ORIGINS`.

## Wichtige Environment-Variablen

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `AUTH_COOKIE_SECURE`
- `AUTH_COOKIE_SAMESITE`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `WHISPER_MODEL`

## API

- `POST /api/register/`
- `POST /api/login/`
- `POST /api/logout/`
- `POST /api/token/refresh/`
- `GET/POST /api/quizzes/`
- `GET/PATCH/DELETE /api/quizzes/{id}/`
- `GET/PATCH /api/quizzes/{id}/progress/`

## Fehlerbehebung

- `FFmpeg is required and was not found.`: FFmpeg installieren und `ffmpeg -version` prüfen.
- `GEMINI_API_KEY is not configured.`: Key in `backend/.env` setzen.
- Browser erhält `401`: neu einloggen oder Cookie-Origin/CORS prüfen.
- Whisper ist langsam: kleineres `WHISPER_MODEL` wie `base` oder `tiny` verwenden.
