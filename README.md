# FastAPI Blog

A full-stack blog application built with FastAPI, async SQLAlchemy, PostgreSQL, and Jinja2 templates.

## Features

- User registration and authentication with JWT Bearer tokens
- Create, read, update, and delete blog posts
- Profile picture upload (local filesystem or Azure Blob Storage)
- Password reset via email
- Server-side rendered pages (Jinja2) alongside a REST API
- Cursor-based pagination for post listings

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.128 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL via psycopg3 |
| Migrations | Alembic |
| Auth | PyJWT + Argon2 (pwdlib) |
| Templates | Jinja2 |
| Email | aiosmtplib |
| Image processing | Pillow |
| Storage | Local filesystem / Azure Blob Storage |
| Package manager | uv |

## Project Structure

```
├── main.py              # App entry point, Jinja2 page routes, exception handlers
├── models.py            # SQLAlchemy models: User, Post, PasswordResetToken
├── schemas.py           # Pydantic DTOs for requests and responses
├── auth.py              # JWT creation/verification, password hashing, dependencies
├── config.py            # Settings loaded from .env via pydantic-settings
├── database.py          # Async engine, session factory, get_db dependency
├── email_utils.py       # Async password reset email via aiosmtplib
├── image_utils.py       # Image resize/crop and storage abstraction (local/Azure)
├── routers/
│   ├── posts.py         # /api/posts — CRUD
│   └── users.py         # /api/users — registration, login, profile, password reset
├── alembic/             # Migration scripts
├── static/              # CSS, favicon, PWA manifest
└── templates/           # Jinja2 HTML templates
```

## Running Locally

**Requirements:** Python 3.12+, uv, PostgreSQL.

```bash
cp .env.example .env
# fill in .env values

uv sync
uv run alembic upgrade head
uv run fastapi dev main.py
```

App available at `http://localhost:8000`, Swagger UI at `http://localhost:8000/docs`.

## Running with Docker

```bash
docker compose up --build
```

Migrations run automatically before the server starts. App at `http://localhost:8000`.

```bash
docker compose down        # stop and remove containers
docker compose down -v     # also delete database and media volumes
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async URL | required |
| `SECRET_KEY` | JWT signing secret | required |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |
| `RESET_TOKEN_EXPIRE_MINUTES` | Password reset token lifetime | `10` |
| `MAIL_SERVER` | SMTP hostname | `localhost` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | SMTP username | `""` |
| `MAIL_PASSWORD` | SMTP password | `""` |
| `MAIL_FROM` | Sender address | `noreply@example.com` |
| `MAIL_USE_TLS` | Enable STARTTLS | `true` |
| `FRONTEND_URL` | Base URL used in email links | `http://localhost:8000` |
| `STORAGE_TYPE` | `local` or `azure` | `local` |
| `AZURE_STORAGE_ACCOUNT_NAME` | Azure storage account | — |
| `AZURE_STORAGE_ACCOUNT_KEY` | Azure connection string | — |
| `AZURE_STORAGE_CONTAINER_NAME` | Blob container name | `profile-pictures` |
| `MAX_UPLOAD_SIZE_BYTES` | Max profile picture size | `5242880` (5 MB) |
| `POSTS_PER_PAGE` | Default API page size | `10` |

## API Reference

### Users — `/api/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/users` | — | Register |
| `POST` | `/api/users/token` | — | Login, returns JWT |
| `GET` | `/api/users/me` | Bearer | Current user profile |
| `PATCH` | `/api/users/me/password` | Bearer | Change password |
| `POST` | `/api/users/forgot-password` | — | Send reset email |
| `POST` | `/api/users/reset-password` | — | Reset password with token |
| `GET` | `/api/users/{id}` | — | Public user profile |
| `PATCH` | `/api/users/{id}` | Bearer | Update username / email |
| `DELETE` | `/api/users/{id}` | Bearer | Delete account |
| `PATCH` | `/api/users/{id}/picture` | Bearer | Upload profile picture |
| `DELETE` | `/api/users/{id}/picture` | Bearer | Remove profile picture |

### Posts — `/api/posts`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/posts?skip=0&limit=10` | — | Paginated post list |
| `POST` | `/api/posts` | Bearer | Create post |
| `GET` | `/api/posts/{id}` | — | Single post |
| `PUT` | `/api/posts/{id}` | Bearer | Full replace |
| `PATCH` | `/api/posts/{id}` | Bearer | Partial update |
| `DELETE` | `/api/posts/{id}` | Bearer | Delete post |

## Database Schema

```
users
  id            INTEGER PK
  username      VARCHAR(50) UNIQUE NOT NULL
  email         VARCHAR(120) UNIQUE NOT NULL
  password_hash VARCHAR(200) NOT NULL
  image_file    VARCHAR(200) NULL

posts
  id            INTEGER PK
  title         VARCHAR(100) NOT NULL
  content       TEXT NOT NULL
  user_id       INTEGER FK → users.id
  date_posted   TIMESTAMPTZ DEFAULT now()
  likes         INTEGER DEFAULT 0

password_reset_tokens
  id            INTEGER PK
  user_id       INTEGER FK → users.id
  token_hash    VARCHAR(64) UNIQUE NOT NULL
  expires_at    TIMESTAMPTZ NOT NULL
  created_at    TIMESTAMPTZ DEFAULT now()
```
