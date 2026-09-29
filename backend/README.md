# QuickTicket Backend

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/backend-test.yml?style=flat-square&logo=django&label=backend)](https://github.com/thegamecracks/quickticket/blob/main/backend)

## Installation

This project requires Python 3.14+ and [uv](https://docs.astral.sh/uv/)
for project management.

```sh
/        $ cd backend
/backend $ uv run fastapi dev
```

**Outdated:** `uv run quickticket` provides an entrypoint for django-admin / manage.py.
See the [documentation](https://docs.djangoproject.com/en/6.1/ref/django-admin/#django-admin-runserver)
for CLI reference.

## (Outdated) Using a production settings.py file

`settings.py` is considered a confidential file and is expected to store
hostnames and credentials directly. To avoid accidentally committing these
credentials to the repository, you can create a copy of settings.py in the
project directory and tell Django to load it with the [DJANGO_SETTINGS_MODULE](https://docs.djangoproject.com/en/6.1/topics/settings/#envvar-DJANGO_SETTINGS_MODULE)
environment variable:

```sh
# backend/
# ├── settings.py
# └── .env
#     DJANGO_SETTINGS_MODULE=settings
/backend $ uv run --env-file .env -m quickticket.manage runserver
```

Note that `DJANGO_SETTINGS_MODULE` takes a Python module import path
and so is dependent on Python's [sys.path](https://docs.python.org/3/library/sys.html#sys.path)
for discovering the settings module.
The `uv run quickticket` [entrypoint](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#console-scripts)
isolates itself from the current working directory, so we have to run manage.py
directly with the `-m <path.to.module>` option to ensure the CWD is included
in `sys.path`, hence `-m quickticket.manage runserver`.

## Running tests

```sh
/backend $ uv run pytest
```

## Creating migrations

When updating SQLAlchemy models, you can auto-generate a new migration with Alembic
like so:

```sh
/backend $ uv run alembic revision --autogenerate -m "Add account and address tables"
```

## Resources

Python libraries:
- [alembic](https://alembic.sqlalchemy.org/en/latest/index.html) (database migrations)
- [authlib](https://docs.authlib.org/en/latest/index.html)
- [fastapi](https://fastapi.tiangolo.com/)
- [httpx2](https://pydantic.dev/docs/httpx2/get-started/)
- [joserfc](https://jose.authlib.org/en/guide/jwt/) (JWT parsing and validation)
- [obstore](https://developmentseed.org/obstore/latest/) (S3 client)
- [pillow](https://pillow.readthedocs.io/en/stable/) (image library)
- [psycopg](https://www.psycopg.org/psycopg3/docs/) (PostgreSQL driver used by Django)
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
