# Backend tests

## Seams

A seam is the public boundary a test observes through. Tests live at these
seams, so a refactor that preserves behavior leaves the suite passing.

| Seam | Catches | Misses |
| --- | --- | --- |
| HTTP routes under `/api` | status codes, payloads, authorization, cookies | middleware order, app wiring |
| `ImageService.upload_banner`, `upload_thumbnail`, `get_url` | image processing, dedupe, object key layout | request validation |
| `get_request_limits` | rule matching (method, route shape, root path) given a supplied rule table | enforcement (covered by the 429 tests) |
| Paging params and `assert_keyset_walk` | filter bounds, keyset continuity, page invariants | per-endpoint ordering |
| Auth routes, driven with the client's cookie jar | PKCE verifier against its challenge, state/nonce binding, token and flow cookies, registration side effects | JWT signatures and claims (faked at `TokenValidator`) |

Assert through a seam: read the response body, or the value the service method
returns. When a behavior is only visible behind a private helper, move the
assertion up to the nearest seam in the table rather than importing the helper.

To list the private imports from `src/` that the suite still makes:

```sh
uv run ruff check --preview --select PLC2701 tests/
```

Every hit is either a bug or one of the two accepted exceptions below.

Assert the behavior at the seam in the right column instead of at these
internals:

| Internal | Assert instead |
| --- | --- |
| `_process_image` | `ImageService` results, or the image route |
| `MAX_*` and `MIN_*` constants | the rejection the limit produces |
| Response field counts (`len(data) == 13`) | the response key set, or the fields that matter |
| `inspect.signature`, `str(stmt.compile(...))` | the behavior the signature or SQL enables |
| `TokenValidator`, `OAuth2Client.fetch_token` | the auth flow's outcome, with the provider faked at discovery |

Two accepted exceptions, where no seam observes the behavior:
`_create_ratelimit_headers` in `tests/dependencies/test_ratelimits.py` (pure
header math) and the Postgres branch of `_build_storage_object_upsert` in
`tests/dependencies/test_images.py` (production dialect; SQLite-backed tests
never reach it, so the test asserts the compiled statement's `ON CONFLICT`
clause instead).

`ordered_collection` in `tests/routers/test_paging.py` is not a private import,
but it recomputes the server's sort from the dataset rows, so it is the one
place where a paging assertion can agree with the code by construction.

### Not yet covered

Deliberate gaps, each a candidate seam when its area changes:

- Auth: JWT decoding and claim validation in `dependencies/auth/tokens.py` are faked.
- `tasks/`, `worker.py`, `cli.py`: no route dispatches a task yet, so the
  autouse asynctasq fixtures below are the only coverage.
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
- The `client` fixture speaks `https://test`. The app marks its cookies
  `Secure`, and an http client silently drops them, so a multi-request flow
  would fail at the second request with a missing cookie.
- `tests/dataset.py` is large; don't read it end-to-end. The `dataset` fixture
  exposes `Dataset` sequences (`users`, `addresses`, `organizations`,
  `organization_members`, `venues`, `events`, `tickets`). Filter those in a
  short `uv run python` snippet when you need to know which rows exist, and
  `grep -n` for a specific ID when you need the full row definition:

  ```sh
  uv run python - <<'PY'
  from tests.dataset import create_test_models

  dataset = create_test_models()
  address_owners = {address.user_id for address in dataset.addresses}
  members = {member.user_id for member in dataset.organization_members}
  print([user.id for user in dataset.users if user.id not in address_owners | members])
  PY
  ```

### Inspecting a response

To read a real response body, write a temporary test that uses the `client`
fixture and run it with `-s`:

```sh
uv run pytest tests/tmp_probe.py -q -s
```

Delete the file once the assertion is written. This beats guessing at error
messages or reading library source.

### Auth

`tests/routers/test_auth.py` fakes the network boundary, not the client: the
`openid_provider` fixture supplies a discovery document, so `OAuth2Client`
really builds the authorization URL, and `auth_settings` adds the OpenID and
frontend settings the flow reads. The post-login tests also fake
`OAuth2Client.fetch_token` and `TokenValidator`, then assert what the route
wrote: cookies, the cached verifier, and the registered rows.

`AuthController` in `conftest.py` still replaces `get_user` for every other
test. To exercise the real resolution, delete that override with
`monkeypatch.delitem(app.dependency_overrides, get_user)`.

### asynctasq

`asynctasq_dispatcher` and `asynctasq_driver` are autouse so that no test
connects a real driver or dispatches to a real queue.
`tests/dependencies/test_tasks.py` asserts that wiring, so a change to either
fixture fails there instead of reaching for a live driver.

When a route starts dispatching tasks, assert the dispatch at the route seam
and keep this guard alongside it: it is what keeps the task queue out of the
suite until then.
