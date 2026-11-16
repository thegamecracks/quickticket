# Backend tests

## Seams

A seam is the public boundary a test observes through. Tests live at these
seams, so a refactor that preserves behavior leaves the suite passing.

| Seam | Catches | Misses |
| --- | --- | --- |
| HTTP routes under `/api` | status codes, payloads, authorization, cookies | middleware order, app wiring |
| `ImageService.upload_banner`, `upload_thumbnail`, `get_url` | image processing, dedupe, object key layout | request validation |
| `get_request_limits` | which rate limits apply to a route | enforcement (covered by the 429 tests) |
| Paging params and `assert_keyset_walk` | filter bounds, keyset continuity, page invariants | per-endpoint ordering |

Assert through a seam: read the response body, or the value the service method
returns. When a behavior is only visible behind a private helper, move the
assertion up to the nearest seam in the table rather than importing the helper.

Assert the behavior at the seam in the right column instead of at these
internals:

| Internal | Assert instead |
| --- | --- |
| `_process_image`, `_build_storage_object_upsert` | `ImageService` results, or the image route |
| `MAX_*` and `MIN_*` constants | the rejection the limit produces |
| Response field counts (`len(data) == 13`) | the response key set, or the fields that matter |
| `inspect.signature`, `str(stmt.compile(...))` | the behavior the signature or SQL enables |

Three accepted exceptions, where no seam observes the behavior:
`_create_ratelimit_headers` in `tests/dependencies/test_ratelimits.py` (pure
header math), `ordered_collection` in `tests/routers/test_paging.py`
(re-derives the server's sort from hand-authored dataset rows), and the
Postgres branch of `_build_storage_object_upsert` in
`tests/dependencies/test_images.py` (production dialect; SQLite-backed tests
never reach it).

### Not yet covered

Deliberate gaps, each a candidate seam when its area changes:

- Auth: `AuthController` in `conftest.py` replaces the login flow, so no test
  drives `routers/auth.py` or `dependencies/auth/` end to end.
- `tasks/`, `worker.py`, `cli.py`: mocked wholesale, no seam yet.
- `models/tickets.py`: ticket sales have no behavior tests.

## Fixtures

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
  `raise_for_status()`; compare the response key set when validating payloads.
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
