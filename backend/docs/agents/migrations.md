# Database migrations

Changing a model requires a migration in the same change. `alembic/versions/`
is append-only once migrations may have been applied elsewhere: add a new
revision rather than editing an existing one.

Autogenerate diffs the live database, so regenerate from a clean one. The local
SQLite database is the default whenever `BACKEND__DB__URL` is unset:

```sh
unset BACKEND__DB__URL
rm quickticket.db
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "Describe the change"
```

Read the generated file top to bottom: it must contain only the changes your
model edits imply — no unrelated tables or columns — with any ambiguity Alembic
flagged resolved by hand.

`uv run alembic upgrade head` applies migrations; `uv run alembic downgrade -1`
reverts the latest one.

Background and the full walkthrough: [`README.md`](../../README.md#creating-migrations).
