# QuickTicket Backend

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/backend-test.yml?style=flat-square&logo=fastapi&label=backend)](https://github.com/thegamecracks/quickticket/blob/main/backend)

## Prerequisites

This project requires Python 3.14+ and [uv](https://docs.astral.sh/uv/)
for project management. To install uv:

```sh
# Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quickstart (API documentation only)

Open a terminal and make sure you're in the backend directory. Even without any
settings configured, you can start the webserver and view the API documentation
at http://127.0.0.1:8000/docs (Swagger UI) or http://127.0.0.1:8000/redoc (ReDoc).

```sh
/        $ cd backend
/backend $ uv run fastapi dev
```

## Configuring an OpenID provider

To actually use the backend, you must configure a database and OpenID provider
for authentication. By default, a local quickticket.db file is used for the database.
Run the following command to create and migrate it to the latest database schema:

```sh
/backend $ uv run alembic upgrade head
```

Afterwards, you need an OAuth2 client from your OpenID provider such as
[Google](https://developers.google.com/identity/openid-connect/openid-connect#appsetup),
[Keycloak](https://www.keycloak.org/), or [Authentik](https://goauthentik.io/).
Make a [.env](/example.env) file containing the client ID, secret,
and the provider's auto-discovery URL:

```ini
BACKEND__OPENID__CLIENT_ID=qoBeV9VCmWs2plast4LX
BACKEND__OPENID__CLIENT_SECRET=my-very-long-secret
BACKEND__OPENID__DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration
```

You can now start the webserver and use it from the frontend:

```sh
/backend $ uv run fastapi dev
```

## Running lints and formatting

```sh
/backend $ uv run ruff check --fix
/backend $ uv run ruff format
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
