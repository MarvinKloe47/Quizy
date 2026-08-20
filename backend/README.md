# Quizly Backend

Django REST API fuer Quizly mit JWT-Authentifizierung ueber HTTP-only Cookies,
Quizverwaltung, Fortschrittsspeicherung und echter Quizgenerierung aus
YouTube-Videos.

## Voraussetzungen

- Python 3.14
- FFmpeg global im `PATH`
- Gemini API-Key

FFmpeg wird fuer `yt_dlp`-Audioextraktion und Whisper benoetigt:

```powershell
winget install --id Gyan.FFmpeg -e --source winget
ffmpeg -version
```

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Trage danach in `.env` einen gueltigen `GEMINI_API_KEY` ein. Committe `.env`
niemals.

Wichtige Defaults:

- `GEMINI_MODEL=gemini-3.5-flash`
- `WHISPER_MODEL=base`
- `DB_NAME=db.sqlite3`

## Datenbank

```powershell
python manage.py migrate
python manage.py createsuperuser
```

## Serverstart

```powershell
python manage.py runserver 127.0.0.1:8000
```

Die API ist dann unter `http://127.0.0.1:8000/api/` erreichbar.

## Tests und Checks

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python manage.py test accounts quizzes
python -m pycodestyle --max-line-length=88 .
python -m pyflakes .
```

Die automatisierten Tests mocken externe Dienste. Fuer echte Quizgenerierung
muessen FFmpeg, `yt_dlp`, `openai-whisper`, `google-genai` und ein Gemini-Key
vorhanden sein.

## API

- `POST /api/register/`
- `POST /api/login/`
- `POST /api/logout/`
- `POST /api/token/refresh/`
- `GET /api/quizzes/`
- `POST /api/quizzes/`
- `GET /api/quizzes/{id}/`
- `PATCH /api/quizzes/{id}/`
- `DELETE /api/quizzes/{id}/`
- `GET /api/quizzes/{id}/progress/`
- `PATCH /api/quizzes/{id}/progress/`

Quiz-Erstellung erwartet:

```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

## CORS und Frontend-Kompatibilitaet

Das Backend ist auf ein lokales Referenz-Frontend vorbereitet. Falls der
Frontend-Origin abweicht, setze in `.env`:

```text
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
```

Cookies werden ueber diese Variablen gesteuert:

- `AUTH_COOKIE_SECURE`
- `AUTH_COOKIE_SAMESITE`
- `AUTH_COOKIE_PATH`

## Environment-Variablen

Siehe `.env.example` fuer alle konfigurierbaren Werte:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `AUTH_COOKIE_SECURE`
- `AUTH_COOKIE_SAMESITE`
- `AUTH_COOKIE_PATH`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `WHISPER_MODEL`
- `DB_ENGINE`
- `DB_NAME`

## Fehlerbehebung

- `FFmpeg is required and was not found.`: FFmpeg installieren und `PATH`
  pruefen.
- `GEMINI_API_KEY is not configured.`: Key in `backend/.env` setzen.
- `Gemini request failed.`: Modell, Key, Kontingent und Gemini-Verfuegbarkeit
  pruefen.
- Browser erhaelt `401`: neu einloggen oder Cookie-Origin/CORS pruefen.
- Whisper ist langsam: kleineres `WHISPER_MODEL` wie `tiny` verwenden.
