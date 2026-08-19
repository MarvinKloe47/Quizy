# Quizly Backend

Das Backend ist ein Django-REST-API-Projekt mit JWT-Authentifizierung über HTTP-only Cookies, Quizverwaltung und einer YouTube-zu-Quiz-Pipeline.

## Schnellstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Vor echter Quizgenerierung müssen FFmpeg global installiert und `GEMINI_API_KEY` in `.env` gesetzt sein.

## Qualität

```powershell
python manage.py check
python manage.py test accounts quizzes
python -m pycodestyle --max-line-length=88 .
```
