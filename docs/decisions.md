# Architectural Decisions

This document explains the key technical choices made in this project and the reasoning behind each one.

---

## Authentication: JWT Bearer tokens, not sessions

**Choice:** Stateless JWT tokens stored in the browser (localStorage), verified on every request.

**Why:** A session-based approach requires server-side state (a session store or database lookups on every request). JWT tokens are self-contained: the server only needs the secret key to verify them, with no database round-trip per request.

**Trade-off:** Token revocation is harder. A JWT stays valid until it expires even after logout. The current token lifetime is 30 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`), which limits the window of exposure. For a blog with no high-security actions after login, this is acceptable.

---

## Password hashing: Argon2 (pwdlib)

**Choice:** `pwdlib[argon2]` with `PasswordHash.recommended()` defaults.

**Why:** Argon2 won the Password Hashing Competition (2015) and is the current best practice. It is resistant to GPU and ASIC attacks due to its configurable memory cost. bcrypt and scrypt are older alternatives that are still secure, but Argon2 is preferred for new projects.

---

## Password reset tokens: hashed in the database

**Choice:** The token sent to the user via email is never stored in plaintext. Only its SHA-256 hash is stored in the `password_reset_tokens` table.

**Why:** If an attacker gains read access to the database, they cannot use the stored values to reset passwords. SHA-256 is used here (not Argon2) because reset tokens are already high-entropy random strings (`secrets.token_urlsafe(32)` = 256 bits of entropy), so a fast hash is sufficient — there is nothing to gain from a slow hash on a value that cannot be brute-forced.

**Additional measures:**
- Old tokens for a user are deleted before issuing a new one (prevents token accumulation).
- All tokens for a user are deleted on password change (invalidates any outstanding reset links).
- Tokens expire after 10 minutes (`RESET_TOKEN_EXPIRE_MINUTES`).
- The forgot-password endpoint always returns 202 regardless of whether the email exists, preventing user enumeration.

---

## Storage abstraction: Strategy pattern (local / Azure)

**Choice:** `StorageService` abstract base class with `LocalStorage` and `AzureStorage` implementations, selected at runtime via `STORAGE_TYPE`.

**Why:** Profile pictures need to be stored somewhere that is:
- Accessible by all app instances (rules out local disk in a multi-replica deployment)
- Persistent across container restarts (rules out ephemeral container storage)

Azure Blob Storage solves both for production. Local storage is simpler for development and single-server deployments. The strategy pattern lets both work without changing any other code.

**Image serving:** When `STORAGE_TYPE=local`, images are served directly by FastAPI's `StaticFiles` mount at `/media`. When `STORAGE_TYPE=azure`, images are proxied through the `/images/{filename}` endpoint, which downloads from Azure and streams the bytes — this avoids exposing Azure credentials or SAS tokens to the frontend.

**Image processing:** All uploads are normalized before storage:
- Resized and cropped to 300×300 px (avoids storing arbitrarily large files)
- EXIF orientation applied (prevents rotated photos from mobile cameras)
- Converted to JPEG at 85% quality (predictable format and size)
- Stored with a UUID filename (prevents path traversal and filename collisions)

---

## Async-first: SQLAlchemy async + psycopg3

**Choice:** `create_async_engine`, `AsyncSession`, `async_sessionmaker` throughout; psycopg3 (`psycopg[binary]`) as the PostgreSQL driver.

**Why:** FastAPI is built on asyncio. Using a synchronous ORM inside async route handlers would block the event loop, serializing requests under I/O load. The async stack lets uvicorn handle many concurrent requests on a single thread.

**psycopg3 vs psycopg2:** psycopg3 has native async support. psycopg2 requires `asyncpg` or thread offloading for async use. psycopg3 also has a more modern API aligned with SQLAlchemy 2.0.

**Windows event loop:** psycopg3's async driver requires `SelectorEventLoop`. On Windows, Python 3.8+ defaults to `ProactorEventLoop`. Alembic migrations are run directly with `asyncio.run()`, so `alembic/env.py` sets `WindowsSelectorEventLoopPolicy` on Windows. This guard is not needed in Docker (Linux) where `SelectorEventLoop` is the default.

---

## Migrations: Alembic, not `create_all`

**Choice:** `alembic upgrade head` manages the schema; `Base.metadata.create_all` is never called in production code.

**Why:** `create_all` only creates tables that do not exist — it cannot alter existing tables, add columns, or drop constraints. Alembic tracks which migrations have been applied and runs only the new ones, making deployments safe and repeatable.

**In Docker:** The `entrypoint.sh` runs `alembic upgrade head` before starting uvicorn. This means every container restart automatically applies pending migrations without manual intervention.

---

## Dual rendering: Jinja2 pages + REST API

**Choice:** HTML pages are rendered server-side by Jinja2 templates at `/`, `/posts`, etc. The REST API lives under `/api` and returns JSON.

**Why:** The Jinja2 pages let the app work without a separate frontend build step and are easier to index for search engines. The JSON API under `/api` allows future decoupling (a separate SPA or mobile client) without rewriting the backend.

**Error handling:** The exception handler in `main.py` checks `request.url.path.startswith("/api")` to decide whether to return a JSON error or an HTML error page. This keeps the two surfaces consistent without duplicating handlers.

---

## Package management: uv

**Choice:** `uv` with `pyproject.toml` and a committed `uv.lock`.

**Why:** uv resolves and installs dependencies significantly faster than pip. The locked `uv.lock` file ensures reproducible installs across development, CI, and Docker builds. In the `Dockerfile`, `uv sync --frozen` fails the build if the lock file is out of date, preventing silent dependency drift.

---

## Docker setup

**Base image:** `python:3.12-slim` — small Debian-based image with Python pre-installed.

**uv in Docker:** The uv binary is copied from the official `ghcr.io/astral-sh/uv` image. Dependencies are installed in a separate `RUN` layer before the application code is copied, so rebuilds triggered by code changes do not reinstall packages.

**Entrypoint:** `entrypoint.sh` runs `alembic upgrade head` then starts the server with `exec` (replacing the shell process so SIGTERM reaches uvicorn correctly for graceful shutdown).

**Database readiness:** `docker-compose.yml` uses `depends_on: condition: service_healthy` with a `pg_isready` healthcheck, so the app container starts only after PostgreSQL is accepting connections — avoiding migration failures on a cold first start.

**Volumes:**
- `postgres_data` — persists the PostgreSQL data directory.
- `media_data` — persists uploaded profile pictures at `/app/media` across container restarts.
