# **System Design Document (SDD)**

## **Product: Personal Health Daily Tracker — Project Helios**

## **Version: V1**

## **Date: February 15, 2026**

---

# **1. Design Goals & Principles**

| Principle | Rationale |
|---|---|
| **Simplicity first** | V1 is a personal tracking tool with isolated per-user data; avoid premature abstractions. |
| **API-first** | Decouple backend from any future frontend (web, mobile, CLI). |
| **Snapshot integrity** | Historical evaluations must never silently change. |
| **Extensibility** | Schema and code structure must accommodate new metrics, summaries, and analytics without rewrites. |
| **Convention over configuration** | Use sensible defaults; reduce boilerplate. |

---

# **2. Tech Stack**

| Layer | Technology | Why |
|---|---|---|
| **Language** | Python 3.12+ | Mature ecosystem, fast prototyping, strong typing support. |
| **Framework** | FastAPI | Async, auto-generated OpenAPI docs, Pydantic validation, dependency injection. |
| **ORM** | SQLAlchemy 2.x (async) | Mature, flexible, supports both ORM and raw SQL when needed. |
| **Migrations** | Alembic | De-facto standard for SQLAlchemy migrations. |
| **Database** | PostgreSQL 16 | ACID transactions, robust date/range queries, easy to scale. Supports `UNIQUE` constraints, partial indexes, and `CHECK` constraints natively. |
| **Auth** | Firebase Auth (Email/Password) | Outsourced auth — handles sign-in, credential storage, and token issuance. Zero auth code to maintain in the backend. |
| **Auth Verification** | `firebase-admin` SDK | Server-side ID token verification. Firebase issues JWTs; our backend validates them. |
| **Validation** | Pydantic v2 | Already required by FastAPI; used for all request/response schemas. |
| **Testing** | pytest + httpx (async) | First-class async test support for FastAPI. |
| **Containerization** | Docker + docker-compose | Reproducible dev environment with PostgreSQL. |

---

# **3. High-Level Architecture**

```
┌──────────────────────────────────────────────────────────────┐
│                      Client (Future)                         │
│              Web App / Mobile App / CLI                       │
└──────────┬──────────────────────┬────────────────────────────┘
           │                      │
           │  Email Auth Flow     │  HTTPS / JSON
           │  (handled entirely   │  Authorization: Bearer <Firebase ID Token>
           │   by Firebase SDK)   │
           ▼                      ▼
┌────────────────────┐   ┌─────────────────────────────────────┐
│   Firebase Auth    │   │          API Gateway Layer          │
│   (External)       │   │           (FastAPI App)             │
│                    │   │                                     │
│  • Sign in users   │   │  ┌────────────┐ ┌────────────────┐  │
│  • Manage creds    │   │  │ Logs Router│ │ Targets Router │  │
│  • Issue ID Token  │   │  └─────┬──────┘ └──────┬─────────┘  │
│  • Manage users    │   │        │               │            │
└────────────────────┘   │        ▼               ▼            │
                         │  ┌──────────────────────────────┐   │
                         │  │       Service Layer          │   │
                         │  │  DailyLogService │ TargetSvc │   │
                         │  └────────────┬─────────────────┘   │
                         │               │                     │
                         │  ┌────────────▼─────────────────┐   │
                         │  │     Repository Layer         │   │
                         │  │  UserRepo │ DailyLogRepo │   │   │
                         │  │  TargetConfigRepo            │   │
                         │  └────────────┬─────────────────┘   │
                         │               │                     │
                         └───────────────┼─────────────────────┘
                                         │  SQLAlchemy (async)
                                         ▼
                              ┌─────────────────────┐
                              │    PostgreSQL 16     │
                              │                     │
                              │  users              │
                              │  target_configs     │
                              │  daily_logs         │
                              └─────────────────────┘
```

### **Layer Responsibilities**

| Layer | Responsibility |
|---|---|
| **Router** | HTTP concerns only — parse request, call service, return response. No business logic. |
| **Service** | All business logic, orchestration, validation rules, target-snapshot logic. |
| **Repository** | Database access only — queries, inserts, updates. Returns ORM models. |
| **Models (SQLAlchemy)** | Table definitions, relationships, constraints. |
| **Schemas (Pydantic)** | Request/response validation, serialization. |

---

# **4. Database Design**

## **4.1 Entity Relationship Diagram**

```
┌──────────────────┐       1:1        ┌──────────────────┐
│     users        │──────────────────│  target_configs   │
│──────────────────│                  │──────────────────│
│ id (PK)          │                  │ id (PK)          │
│ firebase_uid (UQ)│       1:N        │ user_id (FK, UQ) │
│ email            │──────────┐       │ calorie_target   │
│ created_at       │          │       │ protein_target   │
└──────────────────┘          │       │ sleep_target     │
                              │       │ updated_at       │
                              │       └──────────────────┘
                              │
                              │       ┌──────────────────────────┐
                              └──────▶│      daily_logs          │
                                      │──────────────────────────│
                                      │ id (PK)                  │
                                      │ user_id (FK)             │
                                      │ date                     │
                                      │ calories_actual          │
                                      │ protein_actual           │
                                      │ sleep_actual             │
                                      │ workout_completed        │
                                      │ is_period_day            │
                                      │ calorie_target_snapshot  │
                                      │ protein_target_snapshot  │
                                      │ sleep_target_snapshot    │
                                      │ created_at               │
                                      │ updated_at               │
                                      │                          │
                                      │ UQ(user_id, date)        │
                                      └──────────────────────────┘
```

## **4.2 Table Definitions**

### **users**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | Internal ID. Avoids sequential exposure. |
| `firebase_uid` | `VARCHAR(128)` | NOT NULL, UNIQUE | Firebase Auth UID. Used to map Firebase tokens to local user rows. |
| `email` | `VARCHAR(255)` | NOT NULL, UNIQUE | Email address from Firebase. Synced from Firebase on first login. |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

### **target_configs**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `user_id` | `UUID` | FK → users.id, UNIQUE, NOT NULL | One config per user. |
| `calorie_target` | `INTEGER` | NOT NULL, CHECK ≥ 0 | |
| `protein_target` | `INTEGER` | NOT NULL, CHECK ≥ 0 | |
| `sleep_target` | `NUMERIC(4,2)` | NOT NULL, CHECK ≥ 0 | Allows e.g. 8.50 hours. |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |

### **daily_logs**

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `UUID` | PK, default `gen_random_uuid()` | |
| `user_id` | `UUID` | FK → users.id, NOT NULL | |
| `date` | `DATE` | NOT NULL | |
| `calories_actual` | `INTEGER` | NULL, CHECK ≥ 0 | Nullable — partial logging allowed. |
| `protein_actual` | `INTEGER` | NULL, CHECK ≥ 0 | |
| `sleep_actual` | `NUMERIC(4,2)` | NULL, CHECK ≥ 0 | |
| `workout_completed` | `BOOLEAN` | NOT NULL, default `false` | |
| `is_period_day` | `BOOLEAN` | NOT NULL, default `false` | |
| `calorie_target_snapshot` | `INTEGER` | NOT NULL, CHECK ≥ 0 | Frozen at log creation. |
| `protein_target_snapshot` | `INTEGER` | NOT NULL, CHECK ≥ 0 | |
| `sleep_target_snapshot` | `NUMERIC(4,2)` | NOT NULL, CHECK ≥ 0 | |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, default `now()` | Auto-updated on modification. |

**Composite unique constraint:** `UNIQUE(user_id, date)` — enforces FR2 (one log per user per date) at the database level.

## **4.3 Indexes**

| Index | Table | Columns | Type | Purpose |
|---|---|---|---|---|
| `ix_daily_logs_user_date` | `daily_logs` | `(user_id, date)` | UNIQUE B-tree | Enforces uniqueness + fast lookup by user+date. |
| `ix_daily_logs_user_date_range` | `daily_logs` | `(user_id, date)` | B-tree | Efficiently serves date-range queries (covered by unique index). |
| `ix_target_configs_user` | `target_configs` | `(user_id)` | UNIQUE B-tree | Fast config lookup per user. |
| `ix_users_firebase_uid` | `users` | `(firebase_uid)` | UNIQUE B-tree | Map Firebase token → local user. |
| `ix_users_email` | `users` | `(email)` | UNIQUE B-tree | Prevent duplicate email registrations. |

## **4.4 Why Not a Target History Table?**

The PRD specifies snapshot-in-log. A separate `target_history` table that tracks every target change was considered but **rejected for V1** because:

1. The snapshot stored inside each `daily_log` row is the single source of truth for evaluation.
2. A history table would add write complexity with no V1 consumer.
3. It can be added in V2 non-destructively if trend-of-targets becomes a feature.

---

# **5. API Design**

Base URL: `/api/v1`

All endpoints (except auth) require `Authorization: Bearer <token>` header.

## **5.1 Authentication (Outsourced to Firebase)**

Authentication is handled **entirely by Firebase Auth on the client side**. The backend has **no auth endpoints** — no register, login, or refresh routes.

### **Client-Side Flow (Firebase SDK)**

1. Client calls Firebase SDK → `signInWithEmailAndPassword(email, password)`.
2. Firebase validates credentials and returns a Firebase ID Token.
4. Client sends ID Token in `Authorization: Bearer <firebase_id_token>` header on every API request.
5. Firebase SDK handles token refresh automatically (tokens expire after ~1 hour).

### **Server-Side Flow (on every request)**

1. Extract `Bearer` token from `Authorization` header.
2. Call `firebase_admin.auth.verify_id_token(token)` → returns decoded claims including `uid` and `email`.
3. Look up local `users` row by `firebase_uid`.
4. **Auto-provision:** If no local user exists, create one (first-time login). This eliminates a separate registration step.
5. Inject `user_id` (our internal UUID) into the request context via FastAPI dependency.

### **Auto-Provisioned User Response (first API call):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-02-15T00:00:00Z"
}
```

---

## **5.2 Target Configuration**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/targets` | Get current targets. |
| `PUT` | `/targets` | Update targets (upsert). Triggers today's snapshot update. |

### `PUT /targets`

**Request:**
```json
{
  "calorie_target": 2000,
  "protein_target": 150,
  "sleep_target": 7.5
}
```

**Response (200):**
```json
{
  "calorie_target": 2000,
  "protein_target": 150,
  "sleep_target": 7.5,
  "updated_at": "2026-02-15T10:30:00Z"
}
```

**Side effect (FR6):** If a Daily Log exists for today's date, its snapshot fields are updated within the same transaction.

---

## **5.3 Daily Logs**

| Method | Endpoint | Description |
|---|---|---|
| `PUT` | `/logs/{date}` | Create or update log for a date (upsert). |
| `GET` | `/logs/{date}` | Get single log for a date. |
| `GET` | `/logs?start_date=&end_date=` | Get logs in date range. |
| `DELETE` | `/logs/{date}` | Delete a log for a date. |

### Date format: `YYYY-MM-DD`

### `PUT /logs/{date}`

**Request (all metric fields optional for partial update):**
```json
{
  "calories": 1850,
  "protein": 140,
  "sleep": 7.25,
  "workout_completed": true,
  "is_period_day": false
}
```

**Response (200 for update / 201 for create):**
```json
{
  "id": "uuid",
  "date": "2026-02-15",
  "calories": 1850,
  "protein": 140,
  "sleep": 7.25,
  "workout_completed": true,
  "is_period_day": false,
  "targets": {
    "calorie_target": 2000,
    "protein_target": 150,
    "sleep_target": 7.5
  },
  "created_at": "2026-02-15T10:00:00Z",
  "updated_at": "2026-02-15T10:30:00Z"
}
```

**Upsert behavior:**
- **Create:** Snapshot is populated from current `target_configs`.
- **Update:** Only provided fields are modified. Snapshot is NOT re-evaluated (preserves FR6 — only target changes propagate to today).

### `GET /logs?start_date=2026-02-01&end_date=2026-02-15`

**Response (200):**
```json
{
  "logs": [
    {
      "id": "uuid",
      "date": "2026-02-01",
      "calories": 1900,
      "protein": 130,
      "sleep": 6.5,
      "workout_completed": true,
      "is_period_day": false,
      "targets": {
        "calorie_target": 2000,
        "protein_target": 150,
        "sleep_target": 7.5
      },
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "count": 1
}
```

### `DELETE /logs/{date}`

**Response (204):** No content.

---

## **5.4 Daily Analysis**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/logs/{date}/analysis` | Get computed analysis for a date. |

### `GET /logs/2026-02-15/analysis`

**Response (200):**
```json
{
  "date": "2026-02-15",
  "metrics": {
    "calories": {
      "actual": 1850,
      "target": 2000,
      "delta": -150,
      "status": "under"
    },
    "protein": {
      "actual": 140,
      "target": 150,
      "delta": -10,
      "status": "under"
    },
    "sleep": {
      "actual": 7.25,
      "target": 7.5,
      "delta": -0.25,
      "status": "under"
    }
  },
  "habits": {
    "workout_completed": true,
    "is_period_day": false
  }
}
```

**Status values:** `"met"` (actual ≥ target), `"under"` (actual < target), `"no_data"` (actual is null).

**Note:** Analysis is computed on-the-fly from stored log data—not stored separately—to avoid stale data issues.

---

# **6. Core Business Logic**

## **6.1 Target Snapshot Flow**

```
User updates targets
        │
        ▼
┌─────────────────────────┐
│  Update target_configs  │
│  for this user          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Does a daily_log exist for TODAY?  │
└────────┬──────────────┬─────────────┘
         │ Yes          │ No
         ▼              ▼
┌─────────────────┐   (done)
│ Update today's  │
│ log snapshot    │
│ fields only     │
└─────────────────┘

All within a single DB transaction.
Past logs: UNTOUCHED.
```

## **6.2 Daily Log Upsert Flow**

```
PUT /logs/{date}
        │
        ▼
┌──────────────────────────────────┐
│  Does a log exist for this date? │
└────────┬───────────────┬─────────┘
         │ Yes           │ No
         ▼               ▼
┌──────────────┐  ┌──────────────────────────┐
│ Update only  │  │ Create new log           │
│ provided     │  │ Snapshot = current       │
│ fields       │  │ target_configs values    │
│              │  │ + provided metric fields │
│ Snapshot     │  └──────────────────────────┘
│ unchanged    │
└──────────────┘
```

## **6.3 Analysis Computation Rules**

For each quantitative metric:

```
delta  = actual - target_snapshot
status = "no_data"  if actual is NULL
       = "met"      if actual >= target_snapshot
       = "under"    if actual < target_snapshot
```

Analysis is **stateless** — always derived from the log row. No separate analysis table.

---

# **7. Project Structure**

```
project-helios/
├── alembic/                        # Database migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app factory, lifespan, middleware
│   ├── config.py                   # Settings via pydantic-settings (env vars)
│   ├── database.py                 # Async engine, session factory
│   ├── dependencies.py             # FastAPI dependency injection (get_db, get_current_user)
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── target_config.py
│   │   └── daily_log.py
│   │
│   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── target.py
│   │   ├── daily_log.py
│   │   └── analysis.py
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── user_repo.py
│   │   ├── target_config_repo.py
│   │   └── daily_log_repo.py
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── target_service.py
│   │   ├── daily_log_service.py
│   │   └── analysis_service.py
│   │
│   ├── firebase.py                 # Firebase Admin SDK initialization
│   │
│   └── routers/                    # API route handlers
│       ├── __init__.py
│       ├── targets.py
│       ├── daily_logs.py
│       └── analysis.py
│
├── firebase-service-account.json   # Firebase credentials (gitignored)
├── tests/
│   ├── conftest.py                 # Shared fixtures (test DB, mock Firebase token)
│   ├── test_targets.py
│   ├── test_daily_logs.py
│   └── test_analysis.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

### **Why this structure?**

- **Router → Service → Repository** keeps each layer testable in isolation.
- Services can be unit-tested with mocked repositories.
- Repositories can be integration-tested against a real DB.
- Routers are thin — only tested via API-level integration tests.

---

# **8. Authentication & Authorization**

## **8.1 Strategy: Outsourced to Firebase Auth**

All user authentication is delegated to **Firebase Auth (Email/Password provider)**. The backend performs **zero** auth operations — no password storage, no credential verification, no token issuance.

| Responsibility | Handled By |
|---|---|
| Email/password sign-in | Firebase Auth |
| Credential storage and hashing | Firebase Auth |
| Token issuance (JWT) | Firebase Auth |
| Token refresh | Firebase Client SDK (automatic) |
| Token verification | Backend via `firebase-admin` SDK |
| User provisioning | Backend (auto-create on first verified request) |

## **8.2 Firebase ID Token (issued by Firebase)**

Decoded payload (relevant fields):

```json
{
  "sub": "firebase-uid-string",
  "email": "user@example.com",
  "iat": 1739998200,
  "exp": 1740001800,
  "iss": "https://securetoken.google.com/<project-id>",
  "aud": "<firebase-project-id>"
}
```

Tokens are **RS256-signed** by Google and verified using Google's public keys (rotated automatically by the `firebase-admin` SDK).

## **8.3 Auth Flow**

```
Client: Firebase SDK → Email sign-in → get ID Token
  │
  │  Authorization: Bearer <firebase_id_token>
  ▼
Backend: verify_id_token(token)
  │
  ├─ Valid → extract firebase_uid, email
  │    │
  │    ├─ User exists in DB? → inject user_id into request
  │    │
  │    └─ User NOT in DB? → auto-create user row → inject user_id
  │
  └─ Invalid/Expired → return 401 UNAUTHORIZED
```

## **8.4 Auto-Provisioning Logic**

On the **first authenticated API call**, if no `users` row exists for the `firebase_uid`:

1. Insert new row: `firebase_uid`, `email` (from token), `created_at`.
2. This replaces a traditional "register" endpoint.
3. Subsequent requests find the existing row by `firebase_uid`.

This is implemented as a **FastAPI dependency** (`get_current_user`) that runs on every protected route.

## **8.5 Authorization**

All data queries are scoped by `user_id` (internal UUID) extracted after Firebase token verification. There are no roles or permissions in V1 — every authenticated user accesses only their own data. This is enforced at the **repository layer** by requiring `user_id` on every query.

## **8.6 Why Firebase Auth?**

| Benefit | Detail |
|---|---|
| **Zero backend auth code** | No password hashing, no credential verification, and no token generation to build or maintain in our API. |
| **Email auth out of the box** | Firebase handles account sign-in, password storage, and recovery flows. |
| **Low operational overhead** | Suitable for a small personal tracker without building a custom auth service. |
| **Client SDK maturity** | SDKs for Web, iOS, Android, Flutter — any future frontend works instantly. |
| **Migration path** | If needed later, Firebase users can be exported or replaced with another provider. Backend only depends on token verification. |

---

# **9. Error Handling**

## **9.1 Standard Error Response**

```json
{
  "error": {
    "code": "DAILY_LOG_NOT_FOUND",
    "message": "No daily log found for date 2026-02-15.",
    "details": null
  }
}
```

## **9.2 Error Codes**

| HTTP Status | Error Code | When |
|---|---|---|
| `400` | `VALIDATION_ERROR` | Pydantic validation failure (negative values, bad date format, etc.). |
| `401` | `UNAUTHORIZED` | Missing, invalid, or expired Firebase ID token. |
| `404` | `DAILY_LOG_NOT_FOUND` | GET/DELETE log for a date with no entry. |
| `404` | `TARGETS_NOT_CONFIGURED` | GET targets before any have been set. |
| `409` | `LOG_ALREADY_EXISTS` | Should not occur with upsert, but reserved. |
| `422` | `UNPROCESSABLE_ENTITY` | Semantically invalid input (e.g., sleep = 25.0). |
| `500` | `INTERNAL_ERROR` | Unexpected server error. |

## **9.3 Validation Rules Summary**

| Field | Rule |
|---|---|
| `calories` | Integer, ≥ 0, nullable |
| `protein` | Integer, ≥ 0, nullable |
| `sleep` | Decimal, ≥ 0, ≤ 24.0, nullable |
| `workout_completed` | Boolean, defaults to `false` |
| `is_period_day` | Boolean, defaults to `false` |
| `calorie_target` | Integer, ≥ 0, required |
| `protein_target` | Integer, ≥ 0, required |
| `sleep_target` | Decimal, ≥ 0, ≤ 24.0, required |
| `date` | ISO 8601 date (`YYYY-MM-DD`), must not be in the future |
| `email` | Valid email address (managed by Firebase, not validated by backend) |

---

# **10. Key Design Decisions**

| # | Decision | Rationale |
|---|---|---|
| 1 | **Upsert via PUT** instead of separate POST + PATCH | Simplifies client logic — one endpoint handles create and update. PUT is idempotent, matching the "one log per date" model. |
| 2 | **Snapshot in daily_log row** (not a join to history) | PRD mandates snapshot integrity. Denormalization here is intentional — evaluation never requires a join. |
| 3 | **Analysis computed on-the-fly** (not stored) | Avoids stale data. Log edits automatically reflect in analysis without needing to trigger recalculation. |
| 4 | **Actual metrics are nullable** | Supports partial logging (Edge Case #4). Users can log just workout status without entering calories. |
| 5 | **Target snapshot fields are NOT nullable** | A log cannot exist without a valid evaluation baseline. If no targets are configured, log creation returns an error. |
| 6 | **UUID primary keys** | Prevents enumeration attacks. Safe for distributed systems in the future. |
| 7 | **Date in URL path** (`/logs/2026-02-15`) | Natural, readable, RESTful. Date is the logical identifier for a user's daily log. |
| 8 | **No future-date logging** | Prevents invalid data entry. Targets for future dates are undefined. |
| 9 | **Single target_config row per user** (not versioned) | V1 only needs "current targets." History is preserved in log snapshots. Simpler model. |
| 10 | **Async SQLAlchemy** | Matches FastAPI's async nature. Avoids thread pool overhead for DB I/O. |
| 11 | **Outsourced auth (Firebase)** | Eliminates password management, credential verification, and token issuance from our codebase. Backend only verifies tokens — far less code than a custom auth module. |
| 12 | **Auto-provisioning users** | No register endpoint needed. First valid Firebase token triggers user creation. Frictionless onboarding. |

---

# **11. Transaction Boundaries**

These operations must be **atomic** (single database transaction):

| Operation | Scope |
|---|---|
| **Create daily log** | Read target_configs → Insert daily_log (with snapshot). |
| **Update targets** | Update target_configs → If today's log exists, update its snapshot fields. |
| **Delete daily log** | Single delete, straightforward. |

FastAPI dependency injection provides a session-per-request pattern. The session commits at the end of a successful request and rolls back on exception.

---

# **12. Configuration Management**

All configuration via environment variables, loaded by `pydantic-settings`:

```env
# .env.example

# Database
DATABASE_URL=postgresql+asyncpg://helios:password@localhost:5432/helios_db

# Firebase Auth
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json

# App
APP_ENV=development
DEBUG=true
```

**Note:** `firebase-service-account.json` contains the private key for the Firebase Admin SDK. It must be **gitignored** and provided via secure means in production (e.g., mounted secret, environment variable with JSON content).

---

# **13. Docker Setup**

```yaml
# docker-compose.yml (development)
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: helios
      POSTGRES_PASSWORD: password
      POSTGRES_DB: helios_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://helios:password@db:5432/helios_db
      FIREBASE_PROJECT_ID: your-firebase-project-id
      FIREBASE_SERVICE_ACCOUNT_PATH: /run/secrets/firebase-sa.json
    depends_on:
      - db
    volumes:
      - ./app:/code/app  # Hot reload in dev
      - ./firebase-service-account.json:/run/secrets/firebase-sa.json:ro

volumes:
  pgdata:
```

---

# **14. Testing Strategy**

| Level | Scope | Tools | What's tested |
|---|---|---|---|
| **Unit** | Service layer | pytest, mocked repos | Business logic: snapshot rules, analysis computation, validation. |
| **Integration** | Repository layer | pytest, real test DB | SQL correctness, constraints, upsert behavior. |
| **API (E2E)** | Router → DB | pytest + httpx AsyncClient | Full request lifecycle, auth, error codes, response shapes. |

### **Critical Test Cases**

| # | Test Case | Validates |
|---|---|---|
| 1 | Create log → snapshot matches current targets | FR3 |
| 2 | Update targets → today's log snapshot updates | FR6 |
| 3 | Update targets → yesterday's log snapshot unchanged | FR6 |
| 4 | Two logs for same date → 409 or upsert works | FR2 |
| 5 | Partial log (only workout) → other fields null | Edge Case #4 |
| 6 | Create past-date log → snapshot uses *current* targets | Edge Case #2 |
| 7 | Delete log → re-create for same date succeeds | Edge Case #3 |
| 8 | Analysis with null actuals → status = "no_data" | FR7 |
| 9 | Negative calorie value → validation error | BR4 |
| 10 | Unauthenticated request → 401 | NFR 8.5 |
| 11 | First request with valid Firebase token → user auto-created | Auto-provisioning |
| 12 | Request with expired Firebase token → 401 | Auth verification |

---

# **15. Future Extensibility (V2+ Considerations)**

These are **not in V1 scope** but the design accommodates them:

| Feature | How the design supports it |
|---|---|
| **New metrics** (e.g., water intake, steps) | Add nullable columns to `daily_logs` + corresponding snapshot fields. Alembic migration. |
| **Weekly/monthly summaries** | Aggregate query on `daily_logs` grouped by week/month. Could add a materialized view later. |
| **Target history** | New `target_change_log` table with effective dates. Non-breaking addition. |
| **Trend analytics** | Read-only queries on existing `daily_logs` data. Possibly a separate analytics service. |
| **Multi-user / sharing** | Already user-scoped. Add roles/permissions layer on top. |
| **Frontend (Web)** | API-first design means any client can consume the existing endpoints. |

---

# **16. Open Questions for Review**

| # | Question | Options | Impact |
|---|---|---|---|
| 1 | **Should past-date log creation use current targets or prompt the user?** | A) Always use current targets (PRD Edge Case #2). B) Warn user that snapshot will use current targets. | UX clarity. |
| 2 | **Should we allow future-date logging?** | A) Block (current design). B) Allow with a flag. | Validation rules. |
| 3 | **Soft delete or hard delete for logs?** | A) Hard delete (current design — simpler). B) Soft delete with `deleted_at`. | Data recovery capability. |
| 4 | **Should targets require all three fields or allow partial updates?** | A) All three required on every PUT (current design). B) PATCH-style partial update. | API flexibility. |
| ~~5~~ | ~~Password reset flow?~~ | **Eliminated** — Firebase handles account recovery natively. | N/A |

---

# **17. Summary**

The system is a **3-layer REST API** (Router → Service → Repository) backed by **PostgreSQL**, built with **FastAPI + SQLAlchemy async**. Authentication is **fully outsourced to Firebase Auth** (email/password) — the backend carries zero auth logic beyond token verification and user auto-provisioning. The core invariant — **target snapshot integrity** — is enforced by storing snapshot values directly in each daily log row and only updating today's snapshot when targets change. Analysis is computed on-the-fly to avoid stale-data bugs. The entire stack is containerized for reproducible development, and the project structure is designed for clean testability and future extensibility.
