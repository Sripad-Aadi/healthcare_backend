# Healthcare Backend

A healthcare backend built with **Django**, **Django REST Framework**, **PostgreSQL**, and **JWT authentication** (djangorestframework-simplejwt).

## Features

- User registration & login with JWT tokens
- Patient management (CRUD, scoped to the authenticated user)
- Doctor management (CRUD)
- Patient-doctor mapping (assign / list / remove)

## Project Structure

```
healthcare_backend/
├── healthcare/          # Project settings, root URLs, exception handler
├── accounts/            # Custom user model, register/login (JWT)
├── patients/            # Patient model + CRUD API
├── doctors/             # Doctor model + CRUD API
├── mappings/            # Patient-doctor assignment API
├── .env                 # Environment variables (not committed)
├── docker-compose.yml   # PostgreSQL service for local development
└── scripts/test_api.py  # End-to-end API test script
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register/` | Register a new user (name, email, password) | No |
| POST | `/api/auth/login/` | Log in, returns JWT access + refresh tokens | No |
| POST | `/api/patients/` | Add a new patient | Yes |
| GET | `/api/patients/` | List patients created by the current user | Yes |
| GET | `/api/patients/<id>/` | Get a specific patient | Yes |
| PUT | `/api/patients/<id>/` | Update a patient | Yes |
| DELETE | `/api/patients/<id>/` | Delete a patient | Yes |
| POST | `/api/doctors/` | Add a new doctor | Yes |
| GET | `/api/doctors/` | List all doctors | Yes |
| GET | `/api/doctors/<id>/` | Get a specific doctor | Yes |
| PUT | `/api/doctors/<id>/` | Update a doctor | Yes |
| DELETE | `/api/doctors/<id>/` | Delete a doctor | Yes |
| POST | `/api/mappings/` | Assign a doctor to a patient (`patient_id`, `doctor_id`) | Yes |
| GET | `/api/mappings/` | List all patient-doctor mappings | Yes |
| GET | `/api/mappings/<patient_id>/` | Get all doctors assigned to a patient | Yes |
| DELETE | `/api/mappings/<id>/` | Remove a doctor from a patient | Yes |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

### 3. Start PostgreSQL

With Docker:

```bash
docker compose up -d
```

Or use any PostgreSQL instance and update `DB_*` variables in `.env`.

### 4. Run migrations and start the server

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # optional, for Django admin
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/api/`.

## Testing

Run the end-to-end test script (server must be running):

```bash
python scripts/test_api.py
```

Or test manually with Postman / curl:

```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"secret123","password_confirm":"secret123"}'

# Login (use the returned access token below)
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secret123"}'

# Create a patient
curl -X POST http://127.0.0.1:8000/api/patients/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Smith","age":30,"gender":"Female","phone_number":"1234567890"}'
```

## Notes

- All sensitive configuration (secret key, DB credentials) is read from environment variables via `.env`.
- Set `USE_SQLITE=1` in `.env` to use SQLite instead of PostgreSQL for quick local development (PostgreSQL remains the default and required setup).
