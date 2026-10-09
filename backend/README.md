# QuickTicket Backend

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/backend-test.yml?style=flat-square&logo=fastapi&label=backend)](https://github.com/thegamecracks/quickticket/blob/main/backend)

## Prerequisites

This project requires Python 3.14+ and [uv](https://docs.astral.sh/uv/)
for local development, or [Docker](https://docs.docker.com/get-started/) / [Podman](https://podman.io/)
if you only need to host the backend.

To install uv:

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

Afterwards, you need an OAuth2 client from an OpenID provider such as
[Google](https://developers.google.com/identity/openid-connect/openid-connect#appsetup),
[Keycloak](https://www.keycloak.org/), or [Authentik](https://goauthentik.io/).
Make a [.env](example.env) file containing the client ID, secret,
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

## Docker

Using Docker or Podman, you can run the backend with additional services including
Redis and PostgreSQL. To do this, create a [.env](example.env) file if you haven't
already, and adjust any passwords in [docker-compose.yml](docker-compose.yml) if desired.

```sh
/backend $ docker compose up
# With Podman:
/backend $ podman compose up
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

## Running lints and formatting

```sh
/backend $ uv run ruff check --fix
/backend $ uv run ruff format
```

## Running tests

```sh
/backend $ uv run pytest
```

## Resources

| Libraries | Descriptions |
|--:|:--|
| [aiosqlite](https://aiosqlite.omnilib.dev/en/stable/) | SQLite driver |
| [alembic](https://alembic.sqlalchemy.org/en/latest/index.html) | Database migrations |
| [authlib](https://docs.authlib.org/en/latest/index.html) | OAuth2 client |
| [fastapi](https://fastapi.tiangolo.com/) | HTTP API framework |
| [httpx2](https://pydantic.dev/docs/httpx2/get-started/) | HTTP client |
| [joserfc](https://jose.authlib.org/en/guide/jwt/) | JWT parsing and validation |
| [limits](https://limits.readthedocs.io/en/stable/) | ratelimiter |
| [obstore](https://developmentseed.org/obstore/latest/) | S3 client |
| [pillow](https://pillow.readthedocs.io/en/stable/) | Image manipulation |
| [psycopg](https://www.psycopg.org/psycopg3/docs/) | PostgreSQL driver |
| [pydantic](https://pydantic.dev/docs/validation/latest/get-started/) | Data validation and serialization |
| [pydantic-extra-types](https://github.com/pydantic/pydantic-extra-types) | Extra validation |
| [pydantic-settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/) | Settings management |
| [pyinstrument](https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi) | Sampling profiler |
| [pytest](https://docs.pytest.org/en/stable/) | Test framework |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/stable/) | Async tests |
| [redis](https://redis.io/docs/latest/develop/clients/redis-py/) | Redis client |
| [ruff](https://docs.astral.sh/ruff/) | Lint and format |
| [starlette-securecookies](https://github.com/thearchitector/starlette-securecookies) | Cookie encryption |
| [sqlalchemy](https://docs.sqlalchemy.org/en/21/) | Database engine and ORM |
| [tzdata](https://tzdata.python.org/) | IANA timezones |
| [uvicorn](https://uvicorn.dev/) | ASGI webserver |

| Services | Descriptions |
|--:|:--|
| [Garage S3](https://garagehq.deuxfleurs.fr/) | Self-hosted S3 |
| [Keycloak](https://www.keycloak.org/guides) | OpenID provider |
| [PostgreSQL](https://www.postgresql.org/docs/current/index.html) | Relational database |
| [Redis](https://redis.io/docs/latest/develop/) | Key-value store |
