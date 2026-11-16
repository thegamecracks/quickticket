# Dependencies

FastAPI dependencies live in `src/quickticket/dependencies/`, one module per
concern, exported as `Annotated` aliases defined at the bottom of the module:

```python
async def get_thing(state: StateDep) -> Thing: ...


ThingDep = Annotated[Thing, Depends(get_thing)]
```

## Write them async

Dependencies are `async def` even when the body never awaits. FastAPI runs a
sync dependency in its threadpool, so it pays a thread hop and can starve the
pool for the requests doing real I/O. A `def` dependency is reserved for work
that genuinely blocks on an I/O primitive with no async equivalent, and
rewriting that call with async primitives is the preferred fix over keeping the
sync dependency.

Keep blocking calls out of dependency bodies for the same reason: use the async
client, driver, or filesystem API. Work that is CPU-bound and cannot be made
async goes through `anyio.to_thread.run_sync` explicitly, as
`dependencies/images.py` does for image processing.

## Configuration

A dependency that reads module-level configuration takes that configuration as
its own dependency, so tests pass their own values instead of monkeypatching
the module. `get_request_limits` reading its rules this way is the reference
case.

Tests replace dependencies through `app.dependency_overrides`; see
[`testing.md`](testing.md) for which boundaries are seams.
