# Shared Expenses Audit App

Production-style submission for the Spreetail shared-expenses assignment. It uses Django REST Framework, React, PostgreSQL, JWT auth, a reviewable CSV import pipeline, and traceable ledger-based balances.

## Stack
- Backend: Django 5, Django REST Framework, SimpleJWT
- Frontend: React + TypeScript + Vite
- Database: PostgreSQL in Docker, SQLite fallback for quick local tests
- Tests: pytest + pytest-django

## Local Setup
```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_assignment
```

Open:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/health/

Demo login after seeding: `demo / demo12345`.

## Importing the Assignment CSV
Use the Imports screen and upload `C:\Users\prysh\Downloads\Expenses Export.csv` unchanged. The app stores raw rows, detects anomalies, lets reviewers approve/reject reviewable rows, and generates an import report at `/api/imports/{id}/report/`.

## Tests
```bash
cd backend
pip install -r requirements.txt
pytest
```

## Deployment
Recommended Render deployment:
1. Create a managed PostgreSQL database.
2. Deploy `backend/` as a Python web service with:
   - build: `pip install -r requirements.txt`
   - start: `gunicorn config.wsgi:application`
   - env vars from `.env.example`
3. Deploy `frontend/` as a static site:
   - build: `npm install && npm run build`
   - publish: `dist`
4. Set `VITE_API_BASE_URL` to the deployed backend `/api` URL and `CORS_ALLOWED_ORIGINS` to the frontend URL.

## Repository Shape
Meaningful commits separate foundation, schema/import logic, frontend, tests, and documentation so the live interview can trace why each layer exists.
