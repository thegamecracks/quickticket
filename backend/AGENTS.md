# QuickTicket Backend

This is the backend project for QuickTicket.

## Project lints

Before finishing a change, run the following checks to ensure it will pass CI:

```sh
uv run ruff check --fix        # lints
uv run ruff format             # style
uv run ty check                # type check
uv run coverage run -m pytest  # tests
```

## Extra commands

To measure code coverage after tests, including line numbers of missed coverage:

```sh
uv run coverage report --skip-covered --skip-empty --show-missing
```

To manage database migrations:

```sh
uv run alembic upgrade head                    # apply all migrations
uv run alembic downgrade -1                    # revert the latest migration
uv run alembic revision --autogenerate -m "…"  # generate a new migration
```

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
│   ├── models/              # SQLAlchemy ORM models (base, accounts, events,
│   │                        #   organizations, storage, tickets, venues, money)
│   ├── routers/             # FastAPI API routers: auth, events, notifications,
│   │                        #   organizations, profile, venues
│   ├── dependencies/        # FastAPI dependencies: db, cache, cookies,
│   │                        #   models, ratelimits, state, and auth/*
│   │                        #   (provider, tokens, users, redirects)
│   ├── frontend/            # minimal builtin frontend (testing only)
│   └── alembic/             # Alembic setup + versioned migrations
├── tests/                   # pytest tests (pytest-asyncio for async tests)
├── config/                  # postgresql.conf, redis.conf for Docker services
├── alembic.ini              # Alembic configuration
├── Dockerfile               # uv-based production image for the backend
├── docker-compose.yml       # backend + Redis + PostgreSQL + S3
├── example.env              # template of all BACKEND__* settings
└── pyproject.toml           # project metadata, deps, ruff config
```

## Conventions and gotchas

- Use `uv` exclusively for Python tooling (`uv run …`); do not `pip install`
  or create virtualenvs manually.
- Local development defaults to SQLite (`quickticket.db`) when `BACKEND__DB__URL`
  is unset.
- A `.env` with OpenID settings (client ID/secret/discovery URL) is required for
  any authenticated flow; the app starts fine without it, but only for browsing API docs.
- `src/quickticket/frontend/` is a minimal in-Python test frontend used
  to verify authentication; it is not the real frontend and must not be extended.
- When touching `src/quickticket/routers/`, keep handlers thin: business logic
  in dedicated modules or dependencies, request/response shapes via Pydantic models.

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

### Tests

- Test files are named `test_*.py`, where `*` usually corresponds to the
  package or module under test (e.g. tests for `cache.py` live in
  `tests/test_cache.py`).
- If a test requires a long artifact (e.g. a JSON payload or SQL script),
  place the file in `tests/resources/` and load it from the test.
- Store and use common fixtures in `tests/conftest.py` when they need to be
  shared across test files.
