# QuickTicket Backend

This is the backend project for QuickTicket.

## Prerequisites

- **Python 3.14+** (see `.python-version`)
- **uv** for dependency and environment management — always run project tools
  through `uv run …`, never with a system/global Python
- **Docker/Podman** (optional) for the full stack: PostgreSQL, Redis, Garage S3

## Common commands

```sh
# Install/sync dependencies
uv sync

# Start the dev webserver (hot reload; API docs at /docs and /redoc)
uv run fastapi dev

# Lint (auto-fix) and format
uv run ruff check --fix
uv run ruff format

# Type check (ty from Astral; no config in pyproject.toml yet)
uvx ty check

# Run tests
uv run coverage run -m pytest

# Measure code coverage after tests, including line numbers of missed coverage
uv run coverage report --skip-covered --skip-empty --show-missing

# Database migrations (Alembic)
uv run alembic upgrade head                       # apply all migrations
uv run alembic downgrade -1                       # revert the latest migration
uv run alembic revision --autogenerate -m "…"     # generate a new migration

# Full stack with Docker (backend + Redis + PostgreSQL)
docker compose up
```

CI runs the same checks: `uv run -m pytest`, `uvx ty check`,
`uv run ruff check`, and `uv run ruff format` (as a check, not a fixer).
Run all four locally before finishing a change.

## Configuration

- Settings are defined in `.src/quickticket/settings.py` using
  `pydantic-settings` and read from a `.env` file (see `.example.env`
  for all available variables; never commit a real `.env` or secrets).
- Environment variables use a **double-underscore nesting scheme**,
  e.g. `BACKEND__SECTION__FIELD`.
- Local development defaults to SQLite (`quickticket.db`); the Docker compose
  stack uses PostgreSQL and Redis. Migrations must work on both.
- A `.env` with OpenID settings (client ID/secret/discovery URL) is required for
  any authenticated flow; the app starts fine without it, but only for
  unauthenticated use and API docs browsing.

## Project structure

```
.
├── src/quickticket/
│   ├── app.py               # FastAPI app factory/instance, middleware, lifespan
│   ├── settings.py          # pydantic-settings configuration (BACKEND__* vars)
│   ├── oauth.py             # OpenID/OAuth2 client integration (authlib)
│   ├── cache.py             # cache abstraction (SQLite / Redis backends)
│   ├── logging.py           # logging setup and verbosity levels
│   ├── errors.py            # shared error types (e.g. ForcedResponse)
│   ├── models/              # SQLAlchemy ORM models (accounts, events,
│   │                        #   organizations, venues, storage, money types)
│   ├── routers/             # FastAPI API routers: auth, events, notifications,
│   │                        #   organizations, profile, venues
│   ├── dependencies/        # FastAPI dependencies: db, cache, cookies,
│   │                        #   ratelimits, state, and auth/* (provider,
│   │                        #   tokens, users, redirects)
│   ├── frontend/            # minimal builtin frontend (testing only)
│   └── alembic/             # Alembic setup + versioned migrations
├── tests/                   # pytest tests (pytest-asyncio for async tests)
├── config/                  # postgresql.conf, redis.conf for Docker services
├── docker-compose.yml       # backend + Redis + PostgreSQL (Garage S3 TODO)
├── example.env              # template of all BACKEND__* settings
└── pyproject.toml           # project metadata, deps, ruff config
```

## Conventions and gotchas

- **Ruff** is the only linter/formatter. Run `uv run ruff check --fix` and
  `uv run ruff format` before finishing a change.
- The codebase is **fully async**: use async SQLAlchemy sessions, `httpx2`/
  async clients, and `pytest-asyncio` for tests. Avoid blocking calls in
  request handlers.
- Settings are instantiated at module import time in `app.py`
  (`_settings = Settings()`); changing settings requires restarting the dev
  server.
- **Authentication is external.** Never implement password storage, login
  forms, or credential checks in this backend — identity comes from the OpenID
  provider's ID token via `quickticket.oauth` and `dependencies/auth/`.
- Models are **SQLAlchemy dataclasses** (`Base` derives from
  `MappedAsDataclass`, `kw_only=True`). Their constructors are type-checked,
  so instantiate them with keyword arguments matching the `Mapped[...]`
  annotations; columns without a Python-side `default` are required.
- `src/quickticket/frontend/` is a minimal in-Python test frontend used
  to verify authentication; it is not the real frontend and must not be extended.

### Database migrations

- When changing SQLAlchemy models, always generate an Alembic migration in the
  same change; never edit `alembic/versions/` history destructively once
  migrations may have been applied elsewhere.
- **Review auto-generated migrations carefully** — autogenerate diffs the live
  database and can produce unwanted objects or miss ambiguities. For a clean
  diff, recreate the SQLite database first:
  ```sh
  unset BACKEND__DB__URL
  rm quickticket.db
  uv run alembic upgrade head
  uv run alembic revision --autogenerate -m "Describe the change"
  ```
- New migrations must be reversible where possible (implement `downgrade()`),
  and must not assume PostgreSQL-only or SQLite-only features unless handled
  explicitly (e.g. via dialect checks).

### Tests

- Test files are named `test_*.py`, where `*` usually corresponds to the
  package or module under test (e.g. tests for `cache.py` live in
  `tests/test_cache.py`).
- Do **not** require containers for tests. Prefer self-contained, in-memory
  configurations for external dependencies:
  - Database: SQLAlchemy with an in-memory SQLite database
    (`sqlite+aiosqlite:///:memory:` or the shared-cache in-memory variant).
  - Cache: `quickticket.cache.SQLiteCache` with an in-memory connection
    (`sqlite:///:memory:`).
- If a test is more readable implemented as a long standalone artifact (e.g. a
  long SQL script), place that file in `tests/resources/` and load it from the
  test.
- Store and use common fixtures in `tests/conftest.py` when they need to be
  shared across test files.
- Use `pytest-asyncio` (`@pytest.mark.asyncio`) for async tests.

## Notes for agents

- Use `uv` exclusively for Python tooling (`uv run …`); do not `pip install`
  or create virtualenvs manually.
- When touching `routers/`, keep handlers thin: business logic in dedicated
  modules or dependencies, request/response shapes via Pydantic models.
- Python 3.14 features are available; the project is fully typed and ships
  `py.typed`. Type checking with `uvx ty check` must pass — keep annotations
  accurate when editing existing code.
- Respect the monorepo boundary: work only within `backend/` unless the user
  explicitly asks for otherwise.
