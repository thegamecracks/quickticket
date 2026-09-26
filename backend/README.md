# QuickTicket Backend

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/backend-test.yml?style=flat-square&logo=django&label=backend)](https://github.com/thegamecracks/quickticket/blob/main/backend)

## Installation

This project requires Python 3.14+ and [uv](https://docs.astral.sh/uv/)
for project management.

```sh
/        $ cd backend
/backend $ uv run quickticket migrate
Running migrations:
...
/backend $ uv run quickticket runserver
Watching for file changes with StatReloader
...
Django version 6.1.1, using settings 'quickticket.settings'
Starting WSGI development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

`uv run quickticket` provides an entrypoint for django-admin / manage.py.
See the [documentation](https://docs.djangoproject.com/en/6.1/ref/django-admin/#django-admin-runserver)
for CLI reference.

## Using a production settings.py file

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
