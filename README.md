# Library Management API

A production-style REST API for managing books, authors, users and borrowings, built with **FastAPI**, **SQLAlchemy**, **Alembic** and **PostgreSQL** (compatible with MySQL, and SQLite for tests).

Built as a learning project to demonstrate how a professional FastAPI backend is structured: layered architecture (routers → services → models), dependency injection, JWT authentication, role-based access control, validation, consistent responses, automated tests, Alembic migrations and Docker.

---

## Features

- JWT authentication (`register`, `login`, `me`) with bcrypt password hashing
- Role-Based Access Control — `ADMIN` and `MEMBER` roles
- Authors CRUD, Books CRUD with search, filtering and pagination
- Borrow / return flow with stock validation (`available_copies`)
- Business rules: max 3 active borrowings, 14-day borrow duration, no duplicate active borrowing
- Overdue detection (`GET /api/borrowings/overdue`)
- Consistent envelope responses and centralised exception handling
- Pydantic request validation (email, password strength, ISBN, copy counts, pagination)
- OpenAPI docs (`/docs`, `/redoc`) with auth + response schemas
- Alembic migrations, pytest suite (55 tests), Docker

## Tech Stack

| Layer        | Tool                         |
|--------------|------------------------------|
| Language     | Python 3.12                  |
| Framework    | FastAPI + Uvicorn            |
| ORM          | SQLAlchemy 2.0               |
| Migrations   | Alembic                      |
| Validation   | Pydantic v2                  |
| Auth         | PyJWT + bcrypt               |
| Database     | PostgreSQL (Neon) / MySQL / SQLite (tests) |
| Tests        | pytest + FastAPI TestClient  |
| Infra        | Docker, docker-compose       |

## Architecture

```
Request → Router (HTTP only) → Service (business logic) → Model (SQLAlchemy) → DB
                ↑
         Dependencies (auth / RBAC)
```

- **Routers** (`app/routers/`) are thin — they parse HTTP, call a service, build the envelope response.
- **Services** (`app/services/`) hold all business rules (borrowing, availability, limits, uniqueness).
- **Dependencies** (`app/dependencies/`) provide `get_current_user`, `require_admin`, `require_member`.
- **Schemas** (`app/schemas/`) define Pydantic request/response validation.
- **Core** (`app/core/`) has config, DB session, security helpers, exceptions and envelopes.

### Database schema

```
users:        id, name, email (unique), password_hash, role, is_active, created_at, updated_at
authors:      id, name, bio, created_at, updated_at
books:        id, title, isbn (unique), description, published_year, total_copies,
              available_copies, author_id FK → authors, created_at, updated_at
              (checks: available <= total, available >= 0, total >= 0)
borrowings:   id, user_id FK → users, book_id FK → books, borrowed_at, due_at,
              returned_at, status (BORROWED/RETURNED/OVERDUE), created_at, updated_at
```

## Project Structure

```
├── app/
│   ├── main.py                 # FastAPI app, router wiring, exception handlers
│   ├── core/                   # config, database, security, exceptions, responses, validators
│   ├── models/                 # SQLAlchemy models (user, author, book, borrowing)
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic
│   ├── routers/                # HTTP endpoints
│   └── dependencies/           # auth + RBAC dependencies
├── alembic/                    # migrations (env.py + versions/)
├── tests/                      # pytest suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create your environment file and fill in real values:

```bash
cp .env.example .env
```

`.env` is git-ignored — never commit real secrets.

## Environment Variables

| Variable                    | Description                                        | Example |
|-----------------------------|----------------------------------------------------|---------|
| `DATABASE_URL`              | SQLAlchemy connection string                       | `postgresql://user:pass@host/db` |
| `JWT_SECRET_KEY`            | Strong random secret for signing JWTs              | `openssl rand -hex 32` |
| `JWT_ALGORITHM`             | JWT signing algorithm                              | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime                                   | `1440` |
| `MAX_ACTIVE_BORROWINGS`     | Max simultaneous borrowings per member             | `3` |
| `BORROW_DURATION_DAYS`      | Borrow period in days                              | `14` |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | Max login attempts per IP per minute             | `10` |
| `REGISTER_RATE_LIMIT_PER_MINUTE` | Max register attempts per IP per minute       | `20` |
| `API_PREFIX`                | Global URL prefix                                  | `/api` |

## Migrations

```bash
# after changing a model:
alembic revision --autogenerate -m "describe change"

# apply migrations
alembic upgrade head

# rollback one step
alembic downgrade -1
```

## Running the application

```bash
uvicorn app.main:app --reload
```

```bash
docker compose up            # app only (uses DATABASE_URL from .env, e.g. Neon)
docker compose --profile local up   # app + local PostgreSQL
```

Docs are served at:

- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc
- Health → http://localhost:8000/health

## Running tests

Tests use an in-memory SQLite database, so no PostgreSQL is required:

```bash
pytest
```

## API Overview

All endpoints are prefixed with `/api`.

### Authentication

| Method | Path                     | Access | Description |
|--------|--------------------------|--------|-------------|
| POST   | `/api/auth/register`     | Public | Create a MEMBER account |
| POST   | `/api/auth/login`        | Public | Get a JWT access token |
| GET    | `/api/auth/me`           | Any authenticated | Current user |

### Users

| Method | Path              | Access | Description |
|--------|-------------------|--------|-------------|
| GET    | `/api/users`      | ADMIN  | List users (paginated) |
| GET    | `/api/users/{id}` | ADMIN  | Get a user |

### Authors

| Method | Path                | Access        | Description |
|--------|---------------------|---------------|-------------|
| GET    | `/api/authors`      | Authenticated | List (search + pagination) |
| GET    | `/api/authors/{id}` | Authenticated | Get one |
| POST   | `/api/authors`      | ADMIN         | Create |
| PUT    | `/api/authors/{id}` | ADMIN         | Update |
| DELETE | `/api/authors/{id}` | ADMIN         | Delete (409 if books exist) |

### Books

| Method | Path              | Access        | Description |
|--------|-------------------|---------------|-------------|
| GET    | `/api/books`      | Authenticated | List/search — `?search=&author_id=&available=&page=&page_size=` |
| GET    | `/api/books/{id}` | Authenticated | Get one |
| POST   | `/api/books`      | ADMIN         | Create |
| PUT    | `/api/books/{id}` | ADMIN         | Update |
| DELETE | `/api/books/{id}` | ADMIN         | Delete (409 if borrowing history exists) |

### Borrowings

| Method | Path                                | Access | Description |
|--------|-------------------------------------|--------|-------------|
| POST   | `/api/books/{book_id}/borrow`       | MEMBER | Borrow a book |
| POST   | `/api/borrowings/{id}/return`       | Owner or ADMIN | Return a book |
| GET    | `/api/my/borrowings`                | MEMBER | Active borrowings |
| GET    | `/api/my/borrowings/history`        | MEMBER | Full history |
| GET    | `/api/borrowings`                   | ADMIN  | All borrowings (filter by `status`) |
| GET    | `/api/borrowings/overdue`           | ADMIN  | Overdue borrowings |

## Example API Requests

Register:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"Password@123"}'
```

Login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"Password@123"}'
```

Use the returned token:

```bash
curl http://localhost:8000/api/books?search=python&page=1&page_size=10 \
  -H "Authorization: Bearer <access_token>"
```

Borrow and return:

```bash
curl -X POST http://localhost:8000/api/books/1/borrow -H "Authorization: Bearer <token>"
curl -X POST http://localhost:8000/api/borrowings/1/return -H "Authorization: Bearer <token>"
```

## Authentication Flow

1. `POST /api/auth/register` creates a member; the password is hashed with bcrypt (never stored in plain text).
2. `POST /api/auth/login` verifies credentials and returns `{ "access_token": "..." }`.
3. Every protected call sends `Authorization: Bearer <access_token>`.
4. `get_current_user()` decodes the JWT, loads the user and checks it is active.
5. Failed/missing/invalid tokens → `401`. Exercising a role you don't have → `403`.

## RBAC

| Action                               | ADMIN | MEMBER | Public |
|--------------------------------------|:-----:|:------:|:------:|
| Register / Login                     | ✓     | ✓      | ✓      |
| View authors & books                 | ✓     | ✓      |        |
| Create/update/delete authors & books | ✓     |        |        |
| List all users / all borrowings      | ✓     |        |        |
| Overdue report                       | ✓     |        |        |
| Borrow / return / my borrowings      |       | ✓      |        |
| Return (admin override)              | ✓     |        |        |

## Response Format

Success:

```json
{
  "success": true,
  "message": "Book retrieved successfully",
  "data": { "id": 1, "title": "..." }
}
```

Error:

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": { "isbn": "ISBN must be a valid 10 or 13 digit code" }
}
```

Status codes: `200` OK · `201` Created · `204` No Content · `400` Bad Request · `401` Unauthorized · `403` Forbidden · `404` Not Found · `409` Conflict · `422` Unprocessable Entity · `500` Internal Server Error.

## Borrowing Business Rules

A member can borrow when all of these hold:

1. Authenticated and active account
2. Book exists
3. `available_copies > 0`
4. No existing active borrowing for the same book
5. Fewer than `MAX_ACTIVE_BORROWINGS` (default 3) active borrowings

On borrow: `available_copies -= 1` and a `BORROWED` record is created with `due_at = now + 14 days`.

On return: status → `RETURNED`, `returned_at` set, `available_copies += 1`. A borrowing can only be returned by its owner (or an admin) and cannot be returned twice.

A borrowing is **overdue** when `due_at < now` and `returned_at IS NULL`. Overdue status is derived on the fly at read time (`/my/borrowings`, `/borrowings`, `/borrowings/overdue`) — no background jobs and no writes from read endpoints.