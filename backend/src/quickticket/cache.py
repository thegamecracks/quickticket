import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol, Self

import aiosqlite
from redis.asyncio import Redis

log = logging.getLogger(__name__)


# Adapter pattern
class Cache(Protocol):
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> object: ...
    async def get(self, key: str) -> Any | None: ...
    async def set(
        self,
        key: str,
        value: Any,
        *,
        expiry: timedelta | None = None,
    ) -> object: ...
    async def delete(self, key: str) -> bool: ...
    async def pop(self, key: str) -> Any | None: ...


class RedisCache(Cache):
    def __init__(self, client: Redis) -> None:
        self.client = client

    async def __aenter__(self) -> Self:
        log.debug("Entering %s", type(self).__name__)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        log.debug("Closing %s", type(self).__name__)
        await self.client.aclose()

    async def get(self, key: str) -> Any | None:
        log.debug("cache.get(%r)", key)
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: bytes | bytearray | memoryview[int] | str | float,
        *,
        expiry: timedelta | None = None,
    ) -> None:
        log.debug("cache.set(%r)", key)
        await self.client.set(key, value, ex=expiry)

    async def delete(self, key: str) -> bool:
        log.debug("cache.delete(%r)", key)
        n_deleted = await self.client.delete(key)
        return n_deleted > 0

    async def pop(self, key: str) -> Any | None:
        log.debug("cache.pop(%r)", key)
        return await self.client.getdel(key)


class SQLiteCache(Cache):
    def __init__(self, client: aiosqlite.Connection) -> None:
        self.client = client
        self._created_schema = False

    async def __aenter__(self) -> Self:
        log.debug("Entering %s", type(self).__name__)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        log.debug("Closing %s", type(self).__name__)
        await self.client.close()

    async def _create_schema(self) -> None:
        if self._created_schema:
            return

        log.debug("Creating %s schema", type(self).__name__)
        await self.client.execute(
            """
            CREATE TABLE IF NOT EXISTS kv_cache (
                key TEXT PRIMARY KEY,
                value BLOB,
                expires_at TIMESTAMP
            );
            """
        )
        await self.client.commit()
        self._created_schema = True

    async def get(self, key: str) -> Any | None:
        log.debug("cache.get(%r)", key)
        await self._create_schema()

        c = await self.client.execute(
            "SELECT value FROM kv_cache WHERE key = ?1 AND "
            "(expires_at IS NULL OR expires_at > ?2)",
            (key, datetime.now(UTC).timestamp()),
        )
        row = await c.fetchone()
        if row is not None:
            return row[0]

    async def set(
        self,
        key: str,
        value: bytes | bytearray | memoryview[int] | str | float,
        *,
        expiry: timedelta | None = None,
    ) -> None:
        log.debug("cache.set(%r)", key)
        await self._create_schema()

        expires_at: float | None = None
        if expiry is not None:
            expires_at = (datetime.now(UTC) + expiry).timestamp()

        await self.client.execute(
            "INSERT INTO kv_cache (key, value, expires_at) VALUES (?1, ?2, ?3) "
            "ON CONFLICT DO UPDATE SET value = ?2, expires_at = ?3",
            (key, value, expires_at),
        )
        await self.client.commit()

    async def delete(self, key: str) -> bool:
        log.debug("cache.delete(%r)", key)
        await self._create_schema()

        c = await self.client.execute("DELETE FROM kv_cache WHERE key = ?1", (key,))
        await self.client.commit()
        return c.rowcount > 0

    async def pop(self, key: str) -> Any | None:
        log.debug("cache.pop(%r)", key)
        await self._create_schema()

        c = await self.client.execute(
            "DELETE FROM kv_cache WHERE key = ?1 RETURNING value",
            (key,),
        )
        row = await c.fetchone()
        await self.client.commit()

        if row is not None:
            return row[0]
