# QuickTicket Backend

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/backend-test.yml?style=flat-square&logo=fastapi&label=backend)](https://github.com/thegamecracks/quickticket/blob/main/backend)

## Installation

This project requires Python 3.14+ and [uv](https://docs.astral.sh/uv/)
for project management.

```sh
/        $ cd backend
/backend $ uv run alembic upgrade head  # create/migrate database from .env
/backend $ uv run fastapi dev
```

## Running tests

```sh
/backend $ uv run pytest
```

## Creating migrations

When updating SQLAlchemy models, you can auto-generate a new migration with Alembic
like so:

```sh
/backend $ uv run alembic upgrade head  # ensure database is up to date
/backend $ uv run alembic revision --autogenerate -m "Add table.xyz columns"
```

Make sure to set a suitable message and check the resulting migration file
before committing. **Seriously, check.** Auto-generated migrations are
unreliable since it relies on introspecting the live database schema configured
in settings. This can result in unwanted objects if a previous upgrade failed
or the database schema was modified by hand. Sometimes Alembic will also ask
for manual adjustments inside the file if it cannot unambiguously generate
the migration.

For a clean slate, you can set a local database driver like SQLite (the default)
and re-create the entire database before generating your migration:

```sh
/backend $ unset BACKEND__DB__URL  # or export `sqlite+aiosqlite:///quickticket.db`
/backend $ rm quickticket.db
/backend $ uv run alembic upgrade head
/backend $ uv run alembic revision --autogenerate -m "Add table.xyz columns"
```

If you are confident with your migration script, you can apply your migration
to the database:

```sh
/backend $ uv run alembic upgrade head
```

If you need to revert this migration, run `uv run alembic downgrade -1` to downgrade
the database schema, and then remove your old migration script.
If this fails, you can delete the database and regenerate it with
`uv run alembic upgrade head`.

## Resources

Python libraries:
- [alembic](https://alembic.sqlalchemy.org/en/latest/index.html) (database migrations)
- [authlib](https://docs.authlib.org/en/latest/index.html)
- [fastapi](https://fastapi.tiangolo.com/)
- [httpx2](https://pydantic.dev/docs/httpx2/get-started/)
- [joserfc](https://jose.authlib.org/en/guide/jwt/) (JWT parsing and validation)
- [obstore](https://developmentseed.org/obstore/latest/) (S3 client)
- [pillow](https://pillow.readthedocs.io/en/stable/) (image library)
- [psycopg](https://www.psycopg.org/psycopg3/docs/) (PostgreSQL driver)
- [pydantic](https://pydantic.dev/docs/validation/latest/get-started/)
- [pydantic-settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
- [pytest](https://docs.pytest.org/en/stable/)
- [redis](https://redis.io/docs/latest/develop/clients/redis-py/)
- [sqlalchemy](https://docs.sqlalchemy.org/en/21/)
- [uvicorn](https://uvicorn.dev/) (ASGI webserver)
- [whenever](https://whenever.readthedocs.io/en/latest/) (type-safe datetimes)

External services:
- [Garage S3](https://garagehq.deuxfleurs.fr/)
- [Keycloak](https://www.keycloak.org/guides) (OpenID provider)
- [PostgreSQL](https://www.postgresql.org/docs/current/index.html)
