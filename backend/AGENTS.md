# QuickTicket Backend

Python 3.14 + FastAPI JSON API in `src/quickticket/`, tooled with `uv`.

## Verify before you finish

All four must pass. `check --fix` and `format` rewrite files, so run the set
twice: the second run must report no fixes and no formatting changes.

```sh
uv run ruff check --fix        # lints
uv run ruff format             # style
uv run ty check                # type check
uv run coverage run -m pytest  # tests
```

`uv run coverage report --skip-covered --skip-empty --show-missing` adds missed
line numbers.

## Layout

`src/quickticket/`:

- `routers/` — thin handlers: business logic in dedicated modules or
  dependencies, request/response shapes via Pydantic models.
- `dependencies/` — DI: db, cache, cookies, models, ratelimits, state, auth.
- `models/` — SQLAlchemy ORM: base, accounts, events, organizations, storage,
  tickets, venues, money.
- `tasks/` — functions delegated to worker processes; `alembic/` — migrations;
  `settings.py` (`BACKEND__*` envvars), `cli.py`, `worker.py`, `app.py`.
- `frontend/` — throwaway page for testing auth; real frontend work belongs in
  `../frontend/`.

`tests/` mirrors `src/`: `src/quickticket/models/types.py` →
`tests/models/test_types.py`.

## Deeper docs

- Changing a model → [`docs/agents/migrations.md`](docs/agents/migrations.md).
- Writing or debugging tests → [`docs/agents/testing.md`](docs/agents/testing.md).
- Running the app, SQLite/OpenID setup, Docker, worker → [`README.md`](README.md).
