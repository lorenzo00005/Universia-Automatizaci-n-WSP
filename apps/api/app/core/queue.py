"""Encolado de jobs en Redis (arq). Todo lo lento va al worker."""

from typing import Any, Protocol

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings


class JobQueue(Protocol):
    async def enqueue(self, job: str, **kwargs: Any) -> None: ...


class ArqQueue:
    def __init__(self) -> None:
        self._pool: ArqRedis | None = None

    async def enqueue(self, job: str, **kwargs: Any) -> None:
        if self._pool is None:
            self._pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
        await self._pool.enqueue_job(job, **kwargs)


_queue: JobQueue = ArqQueue()


def get_queue() -> JobQueue:
    return _queue
