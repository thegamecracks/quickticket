# Backend tests

Shared fixtures live in `tests/conftest.py`.

- `make_session` uses `expire_on_commit=False`, and `dataset`/`dataset_loader.dataset`
  are the same per-test object, so ORM objects keep their Python-side attributes
  after `dataset_loader.load()`. Build expected payloads from the seeded objects
  rather than hardcoding values; seeded events rely on model defaults
  (`max_attendees=0`, `ticket_price=Money(amount=0, currency="CAD")`, `tickets=[]`).
- Pydantic value types serialize straight to JSON: compare `Money`/`Point`
  expectations via `.model_dump()`. `Currency` is a `StrEnum` and compares equal
  to its string value.
- Path params typed as `UUID` return 422 for malformed strings and 404 only for
  well-formed-but-missing IDs. For a 404, pass a valid UUID absent from the
  dataset (e.g. `00000000-0000-0000-0000-000000000000`).
- Assert exact status codes (`assert response.status_code == 200`) rather than
  `raise_for_status()`; check `len(data)` when validating payloads.
- `tests/dataset.py` is large; don't read it end-to-end. The `dataset` fixture
  exposes `Dataset` sequences (`users`, `addresses`, `organizations`,
  `organization_members`, `venues`, `events`, `tickets`). Filter those in a
  short `uv run python` snippet when you need to know which rows exist, and
  `grep -n` for a specific ID when you need the full row definition:

  ```sh
  uv run python - <<'PY'
  from tests.dataset import create_test_models

  dataset = create_test_models()
  address_owners = {address.account_id for address in dataset.addresses}
  member_accounts = {member.account_id for member in dataset.organization_members}
  print([user.id for user in dataset.users if user.id not in address_owners | member_accounts])
  PY
  ```
