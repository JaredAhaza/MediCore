# MediCore

Backend for a clinic system built with Django + DRF, using JWT auth and PostgreSQL (Supabase pooler). This README covers the backend setup completed so far.

## Stack
- Django 5
- Django REST Framework
- SimpleJWT (JWT auth)
- PostgreSQL (Supabase session pooler)
- django-cors-headers

## Project Structure (backend)
- `MediCore/settings.py` — project settings
- `users` — custom user model `users.User` with `role`
- `core/management/commands` — test utilities:
  - `test_db`, `test_users`, `test_api`, `run_all_tests`, `clean_test_data`

## Setup

### 1) Create and activate venv
```bash
python -m venv venv
venv\Scripts\activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

If you don’t have a requirements file, install directly:
```bash
pip install Django djangorestframework djangorestframework-simplejwt django-cors-headers psycopg2-binary
```

### 3) Configure database (Supabase session pooler recommended)
Edit `MediCore/settings.py`:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

CORS_ALLOWED_ORIGINS = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]
CORS_ALLOW_CREDENTIALS = True

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': os.getenv('DB_NAME', 'postgres'),
		'USER': os.getenv('DB_USER', ''),
		'PASSWORD': os.getenv('DB_PASSWORD', ''),
		'HOST': os.getenv('DB_HOST', 'localhost'),
		'PORT': os.getenv('DB_PORT', '5432'),
	}
}
```

### 4) Apply migrations and create admin user
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5) Run the server
```bash
python manage.py runserver
```

## Authentication

### Custom User
- Model: `users.User`
- Field: `role` with choices:
  - `ADMIN`, `DOCTOR`, `LAB_TECH`, `PHARMACIST`, `FINANCE`, `PATIENT`

### JWT Endpoints
- `POST /api/token/` — obtain tokens
- `POST /api/token/refresh/` — refresh access token

Example:
```http
POST /api/token/
Content-Type: application/json

{ "username": "admin", "password": "yourpassword" }
```

Use:
```
Authorization: Bearer <access_token>
```

### Helper Endpoint
- `GET /api/auth/me/` — returns current user profile (requires JWT)

## CORS
Configure in `MediCore/settings.py` for Vue dev:
```python
CORS_ALLOWED_ORIGINS = [
	'http://localhost:5173',
	'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True
```

## Test Utilities (Management Commands)
Idempotent by default — they clean prior test data unless `--no-reset` is passed.

- Database connectivity:
```bash
python manage.py test_db
```

- User roles:
```bash
python manage.py test_users
# Skip cleanup:
python manage.py test_users --no-reset
```

- API auth (JWT + protected route):
```bash
python manage.py test_api
# Skip cleanup:
python manage.py test_api --no-reset
```

- Clean test data explicitly:
```bash
python manage.py clean_test_data
```

- Run all tests:
```bash
python manage.py run_all_tests
```

## Next Steps
- Add `patients` app (Patient, Visit models + CRUD)
- EMR modules (LabReport, Prescription, Treatment Notes)
- Finance (Invoice, Payment)
- Audit logs and analytics
- Frontend (Vue 3 + Pinia + Router) and integration

### Environment
Create `backend/.env` (not committed):
- SECRET_KEY, DEBUG, ALLOWED_HOSTS
- CORS_ALLOWED_ORIGINS
- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

This removes hard-coded secrets and keeps your Supabase creds out of git.
