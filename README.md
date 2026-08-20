# Quizly Backend

Quizly ist ein Django REST Backend, das aus einem YouTube-Video automatisch ein
Multiple-Choice-Quiz generiert. Die API verwaltet Benutzerkonten,
JWT-Authentifizierung, Quizze, Fragen und gespeicherten Quizfortschritt.

Pipeline:

```text
YouTube -> yt_dlp -> FFmpeg -> Whisper -> Gemini Flash -> Quiz -> Django REST API
```

## Features

- Registrierung, Login, Logout und Token Refresh
- JWT Access- und Refresh-Tokens in HTTP-only Cookies
- Serverseitige Token-Invalidierung beim Logout
- Quiz erstellen, abrufen, bearbeiten und loeschen
- Quizfortschritt speichern und abrufen
- Benutzerbezogene Zugriffskontrolle
- Django Admin

## Technischer Stack

- Python 3.12 bis 3.14
- Django 6
- Django REST Framework
- Django CORS Headers
- SimpleJWT
- yt_dlp
- FFmpeg
- OpenAI Whisper
- Google Gemini
- SQLite fuer lokale Entwicklung

## Voraussetzungen

Fuer lokale Entwicklung wird Python 3.12 bis 3.14 benoetigt. Lokal wurde das
Backend mit Python 3.14 geprueft. Django 6 unterstuetzt Python 3.12, 3.13 und
3.14.

Zusaetzlich erforderlich:

- FFmpeg global im `PATH`
- Gemini API-Key fuer echte Quizgenerierung

FFmpeg muss global installiert sein, da `yt_dlp` und Whisper die
Audioverarbeitung darueber ausfuehren.

Windows-Beispiel:

```powershell
winget install --id Gyan.FFmpeg -e --source winget
ffmpeg -version
```

## Installation

```powershell
git clone https://github.com/MarvinKloe47/Quizy.git
cd Quizy

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## Environment

Die Datei `.env` bleibt lokal und darf niemals committed werden. Sie wird ueber
`.gitignore` ignoriert. Echte Secrets gehoeren ausschliesslich in die lokale
`.env`.

Beispielwerte stehen in `.env.example`:

```text
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
AUTH_COOKIE_SECURE=False
AUTH_COOKIE_SAMESITE=Lax
AUTH_COOKIE_PATH=/
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash
WHISPER_MODEL=base
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Fuer echte Quizgenerierung muss `GEMINI_API_KEY` lokal gesetzt werden. Das
Whisper-Modell wird ueber `WHISPER_MODEL` konfiguriert; lokal ist `base` der
Standardwert.

## Datenbank

```powershell
python manage.py migrate
```

Optional kann ein Admin-Benutzer erstellt werden:

```powershell
python manage.py createsuperuser
```

Der Django Admin ist nach Serverstart erreichbar unter:

```text
http://127.0.0.1:8000/admin/
```

## Serverstart

```powershell
python manage.py runserver
```

API-Basis-URL:

```text
http://127.0.0.1:8000/api/
```

## API-Endpunkte

Authentication:

- `POST /api/register/`
- `POST /api/login/`
- `POST /api/logout/`
- `POST /api/token/refresh/`

Quiz:

- `GET /api/quizzes/`
- `POST /api/quizzes/`
- `GET /api/quizzes/{id}/`
- `PATCH /api/quizzes/{id}/`
- `DELETE /api/quizzes/{id}/`

Progress:

- `GET /api/quizzes/{id}/progress/`
- `PATCH /api/quizzes/{id}/progress/`

## Quiz-Pipeline

Bei `POST /api/quizzes/` wird die komplette Pipeline ausgefuehrt:

1. Die YouTube-URL wird validiert.
2. `yt_dlp` verarbeitet das Video und laedt die Audiospur.
3. FFmpeg verarbeitet das Audio.
4. Whisper transkribiert das Audio lokal.
5. Gemini Flash generiert aus dem Transkript ein Quiz.
6. Das Ergebnis wird strukturell validiert.
7. Quiz und Fragen werden atomar in Django gespeichert.

Ein generiertes Quiz besteht aus:

- Titel
- Beschreibung
- exakt 10 Fragen
- exakt 4 Antwortmoeglichkeiten pro Frage
- genau einer korrekten Antwort pro Frage

## Beispiel: Quiz-Erstellung

Request:

```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

Die URL muss ein unterstuetzter YouTube-Link sein, zum Beispiel
`youtube.com/watch?v=...` oder `youtu.be/...`.

## Authentifizierung

Der Login setzt Access- und Refresh-JWTs als HTTP-only Cookies. Der
Access-Token authentifiziert API-Requests. Der Refresh-Token kann ueber
`POST /api/token/refresh/` einen neuen Access-Token ausstellen.

Beim Logout werden die Cookies geloescht. Zusaetzlich erhoeht das Backend eine
serverseitige Token-Version, wodurch bereits ausgestellte Tokens des Benutzers
ungueltig werden.

## Tests und Checks

Die automatisierten Tests mocken externe Dienste. Fuer echte Quizgenerierung
muessen FFmpeg, `yt_dlp`, `openai-whisper`, `google-genai` und ein gueltiger
Gemini API-Key vorhanden sein.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --check
python manage.py test accounts quizzes
python -m pycodestyle --max-line-length=88 .
python -m pyflakes .
```

## Projektstruktur

```text
accounts/              Benutzer, Authentifizierung, Cookies, Token-Versionen
  api/                 DRF Serializer, Views und URLs fuer Auth-Endpunkte
quizzes/               Quizmodelle, Pipeline, Validierung und Services
  api/                 DRF Serializer, Views und URLs fuer Quiz-Endpunkte
core/                  Django Settings, Root-URLs, ASGI/WSGI
manage.py              Django Management CLI
requirements.txt       Python-Abhaengigkeiten
.env.example           Beispielkonfiguration ohne Secrets
.gitignore             Lokale Artefakte und Secrets
```

Wichtige Apps:

- `accounts`: Registrierung, Login, Logout, Refresh und Cookie-JWT-Auth
- `quizzes`: Quiz-CRUD, Progress API, YouTube-/Whisper-/Gemini-Pipeline
- `core`: Django-Projektkonfiguration

## Sicherheit

- keine Secrets im Repository
- `.env` wird ignoriert
- JWTs werden als HTTP-only Cookies gesetzt
- API-Zugriff ist standardmaessig authentifiziert
- Benutzer sehen und aendern nur eigene Quizze
- Logout invalidiert bestehende Tokens ueber Token-Versionierung
- Quizgenerierung akzeptiert nur validierte YouTube-Video-URLs
- generierte Quizdaten werden vor dem Speichern validiert

## CORS-Hinweise

Fuer lokale Frontend-Kompatibilitaet sind standardmaessig diese Origins
vorgesehen:

```text
http://127.0.0.1:5500
http://localhost:5500
```

Falls ein anderes Frontend oder ein anderer Port genutzt wird, muessen
`CORS_ALLOWED_ORIGINS` und `CSRF_TRUSTED_ORIGINS` in `.env` entsprechend
angepasst werden.
