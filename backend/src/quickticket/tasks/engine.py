"""Manage global state accessible to task functions.

This state should be set by task queue workers before running tasks.
See src/quickticket/worker.py.

"""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

_engine: AsyncEngine | None = None
_make_session: async_sessionmaker[AsyncSession] | None = None


def register_async_engine(engine: AsyncEngine) -> None:
    """Register an async engine for tasks."""
    global _engine
    _engine = engine


def register_async_sessionmaker(make_session: async_sessionmaker[AsyncSession]) -> None:
    """Register an async sessionmaker for tasks."""
    global _make_session
    _make_session = make_session
    # Base._asynctasq_session_factory = make_session
    # XXX:
    # asynctasq is supposed to have native support for serializing ORM models
    # by primary key. However, it turns out it doesn't work with our models
    # and keeps trying to serialize the entire class.
    #
    # For models with custom types like Money and Point, this results in
    # tasks failing to serialize and dispatch.
    #
    # Here's my guess as to why it doesn't work:
    # 1. asynctasq uses the msgspec serialization library.
    # 2. msgspec natively converts dataclasses to JSON objects.
    # 3. our ORM models are marked as dataclasses.
    # 4. msgspec detects this and serializes the ORM models by its attributes,
    #    instead of calling asynctasq's encoding hook.
    #
    # Therefore, asynctasq doesn't get a chance to serialize by primary key.
    #
    # https://github.com/thegamecracks/quickticket/commit/160f9bf34d9bd831f03779ee68f3408e90176d43
    # We could make asynctasq's TypeHook classes for our custom types,
    # but that doesn't solve the root problem that msgspec won't let asynctasq
    # convert dataclass-mapped ORM models to their primary keys.


def get_async_engine() -> AsyncEngine:
    """Get the async engine used by tasks."""
    if _engine is None:
        raise RuntimeError("AsyncEngine not registered with register_async_engine()")
    return _engine


def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Get the async sessionmaker used by tasks."""
    if _make_session is None:
        raise RuntimeError("Sessionmaker not registered with register_async_sessionmaker()")
    return _make_session
