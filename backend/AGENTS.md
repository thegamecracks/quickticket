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

To run the background task worker:

```sh
uv run quickticket worker
```

## Project structure

```
.
├── src/quickticket/
│   ├── alembic/             # Alembic setup + versioned migrations
│   ├── dependencies/        # FastAPI dependencies: db, cache, cookies,
│   │                        #   models, ratelimits, state, and auth/*
│   │                        #   (provider, tokens, users, redirects)
│   ├── frontend/            # minimal builtin frontend (testing only)
│   ├── models/              # SQLAlchemy ORM models (base, accounts, events,
│   │                        #   organizations, storage, tickets, venues, money)
│   ├── routers/             # FastAPI API routers: auth, events, notifications,
│   │                        #   organizations, profile, venues
│   ├── tasks/               # Task functions delegated to worker processes
│   ├── app.py               # FastAPI app factory/instance, middleware, lifespan
│   ├── cache.py             # cache abstraction (SQLite / Redis backends)
│   ├── cli.py               # CLI to run webservers and task workers
│   ├── errors.py            # shared error types (e.g. ForcedResponse)
│   ├── logging.py           # logging setup and verbosity levels
│   ├── oauth.py             # OpenID/OAuth2 client integration (authlib)
│   ├── settings.py          # pydantic-settings configuration (BACKEND__* vars)
│   ├── validators.py        # Validation helpers for Pydantic models
│   └── worker.py            # Worker initialization for processing tasks
├── config/                  # postgresql.conf, redis.conf for Docker services
├── tests/                   # pytest tests (pytest-asyncio for async tests)
├── alembic.ini              # Alembic configuration
├── compose.yaml             # backend + worker + Redis + PostgreSQL + S3
├── Dockerfile               # uv-based production image for the backend
├── example.env              # template of all envvar settings
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
- The `dataset` fixture and `dataset_loader.dataset` are the same per-test
  object. Because `make_session` uses `expire_on_commit=False`, ORM objects keep
  their Python-side attributes after `dataset_loader.load()`, so expected
  payloads can be built from the seeded objects instead of hardcoding values.
  Seeded events rely on model defaults such as `max_attendees=0`,
  `ticket_price=Money(amount=0, currency="CAD")`, and `tickets=[]`.
- The test database is SQLite and does not preserve timezone offsets for
  `current_timestamp` columns: tz-aware datetimes seeded in
  `tests/resources/data.py` come back naive with the same wall-clock time.
  Compare them with `.replace(tzinfo=None)` (or `datetime.fromisoformat()` on
  the response).
- Pydantic value types serialize straight to JSON: compare `Money`/`Point`
  expectations via `.model_dump()`, and note that `Currency` is a `StrEnum`
  that compares equal to its string value.
- FastAPI path params typed as `UUID` return 422 for malformed strings and 404
  only for well-formed-but-missing IDs. To exercise a 404, pass a valid UUID
  that is not in the dataset (e.g. `uuid7()`), not an arbitrary string.
- Assert exact status codes (e.g. `assert response.status_code == 200`) rather
  than `raise_for_status()`, and check `len(data)` when validating payloads.
