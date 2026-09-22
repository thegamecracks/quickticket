# QuickTicket Backend

# Installation

This project requires Python 3.14+ and [uv](https://docs.astral.sh/uv/)
for project management.

```sh
/        $ cd backend
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
