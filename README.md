# Project Helios — Personal Health Daily Tracker

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16 (or Docker)
- Firebase project with Phone Auth enabled

### 1. Clone & install dependencies

```bash
cd ProjectHelios
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL and FIREBASE_PROJECT_ID
```

### 3. Set up Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a project (or use existing one)
3. Enable **Phone Number** sign-in under Authentication → Sign-in method
4. Generate a service account key: Project Settings → Service Accounts → Generate New Private Key
5. Save the JSON file as `firebase-service-account.json` in the project root

### 4. Start the database

**With Docker:**
```bash
docker-compose up db -d
```

**Or use an existing PostgreSQL instance** — just update `DATABASE_URL` in `.env`.

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

API docs available at: http://localhost:8000/docs

### 7. Run tests

```bash
pytest
```

---

## Project Structure

```
app/
├── main.py              # FastAPI app
├── config.py            # Settings (env vars)
├── database.py          # Async DB engine
├── dependencies.py      # Auth & DB injection
├── firebase.py          # Firebase Admin SDK init
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── repositories/        # Data access layer
├── services/            # Business logic
└── routers/             # API route handlers
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/targets` | Get current targets |
| `PUT` | `/api/v1/targets` | Set/update targets |
| `PUT` | `/api/v1/logs/{date}` | Create/update daily log |
| `GET` | `/api/v1/logs/{date}` | Get daily log |
| `GET` | `/api/v1/logs?start_date=&end_date=` | Get logs by range |
| `DELETE` | `/api/v1/logs/{date}` | Delete daily log |
| `GET` | `/api/v1/logs/{date}/analysis` | Get daily analysis |
