# QuickTicket Backend

Python 3.14 + FastAPI JSON API in `src/quickticket/`, tooled with `uv`.

## Verify before you finish

All four must pass, with nothing left for the tools to change — `check --fix` and `format`
rewrite files, so re-run until clean:

```sh
uv run ruff check --fix        # lints
uv run ruff format             # style
uv run ty check                # type check
uv run coverage run -m pytest  # tests
```

`uv run coverage report --skip-covered --skip-empty --show-missing` adds missed line numbers.

## Layout

`src/quickticket/`:

- `routers/` — thin handlers: business logic in dedicated modules or dependencies,
  request/response shapes via Pydantic models.
- `dependencies/` — DI: db, cache, cookies, models, ratelimits, state, auth.
- `models/` — SQLAlchemy ORM: base, accounts, events, organizations, storage, tickets,
  venues, money.
- `tasks/` — functions delegated to worker processes; `alembic/` — migrations;
  `settings.py` (`BACKEND__*` envvars), `cli.py`, `worker.py`, `app.py`.
- `frontend/` — throwaway page for testing auth; real frontend work belongs in `../frontend/`.

`tests/` mirrors `src/`: `src/quickticket/models/types.py` → `tests/models/test_types.py`.

## Environment

- `uv run fastapi dev` serves the API (`/docs`, `/redoc`); `uv run quickticket worker`
  runs the background task worker.
- Local development uses SQLite (`quickticket.db`) when `BACKEND__DB__URL` is unset.
- Authenticated flows need `.env` with an OpenID client ID/secret/discovery URL
  (see `example.env`); without it the app still starts, for browsing the API docs only.
- Python tooling goes through `uv run …`; dependencies live in `pyproject.toml` + `uv.lock`.

## Database migrations

Changing a model requires a migration in the same change. Add a new file:
`alembic/versions/` history is append-only once migrations may have been applied elsewhere.

Autogenerate diffs the live database, so regenerate from a clean one for a clean diff:

```sh
unset BACKEND__DB__URL
rm quickticket.db
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "Describe the change"
```

Read the generated file top to bottom: it must contain only the changes your model edits
imply — no unrelated tables or columns — with any ambiguity Alembic flagged resolved by hand.

`uv run alembic upgrade head` applies migrations; `uv run alembic downgrade -1` reverts the
latest one.

## Tests

Shared fixtures live in `tests/conftest.py`.

- `make_session` uses `expire_on_commit=False`, and `dataset`/`dataset_loader.dataset` are
  the same per-test object, so ORM objects keep their Python-side attributes after
  `dataset_loader.load()`. Build expected payloads from the seeded objects rather than
  hardcoding values; seeded events rely on model defaults (`max_attendees=0`,
  `ticket_price=Money(amount=0, currency="CAD")`, `tickets=[]`).
- Pydantic value types serialize straight to JSON: compare `Money`/`Point` expectations via
  `.model_dump()`. `Currency` is a `StrEnum` and compares equal to its string value.
- Path params typed as `UUID` return 422 for malformed strings and 404 only for
  well-formed-but-missing IDs. For a 404, pass a valid UUID absent from the dataset
  (e.g. `00000000-0000-0000-0000-000000000000`).
- Assert exact status codes (`assert response.status_code == 200`) rather than
  `raise_for_status()`; check `len(data)` when validating payloads.
