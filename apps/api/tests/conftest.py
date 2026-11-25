"""Fixtures: base de datos de test real (Postgres + pgvector) con migraciones aplicadas."""

import os
import subprocess
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

PG_HOST = os.environ.get("TEST_PG_HOST", "localhost")
PG_PORT = os.environ.get("TEST_PG_PORT", "5432")
PG_SUPER = os.environ.get("TEST_PG_SUPERUSER", "universia")
PG_SUPER_PASS = os.environ.get("TEST_PG_SUPERPASS", "universia")
TEST_DB = "universia_test"

os.environ["DATABASE_URL"] = (
    f"postgresql+asyncpg://universia_app:universia_app@{PG_HOST}:{PG_PORT}/{TEST_DB}"
)
os.environ["DATABASE_MIGRATIONS_URL"] = (
    f"postgresql+asyncpg://{PG_SUPER}:{PG_SUPER_PASS}@{PG_HOST}:{PG_PORT}/{TEST_DB}"
)
os.environ.setdefault("ENCRYPTION_KEY", "q0bz7bS4lF0pLUv2r2E8fV0rQ8cP1n7mXo3t9hY6kJ4=")
os.environ["APP_ENV"] = "test"


async def _prepare_database() -> None:
    dsn = f"postgresql://{PG_SUPER}:{PG_SUPER_PASS}@{PG_HOST}:{PG_PORT}"
    conn = await asyncpg.connect(f"{dsn}/postgres")
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{TEST_DB}"')
        exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = 'universia_app'")
        if not exists:
            await conn.execute("CREATE ROLE universia_app LOGIN PASSWORD 'universia_app'")
    finally:
        await conn.close()
    conn = await asyncpg.connect(f"{dsn}/{TEST_DB}")
    try:
        await conn.execute(
            """
            CREATE EXTENSION IF NOT EXISTS vector;
            GRANT USAGE ON SCHEMA public TO universia_app;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
              GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO universia_app;
            ALTER DEFAULT PRIVILEGES IN SCHEMA public
              GRANT USAGE, SELECT ON SEQUENCES TO universia_app;
            """
        )
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
async def database() -> AsyncIterator[None]:
    await _prepare_database()
    api_dir = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=api_dir, check=True)
    yield
    from app.core.db import get_engine

    await get_engine().dispose()


class FakeQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, dict[str, Any]]] = []

    async def enqueue(self, job: str, **kwargs: Any) -> None:
        self.jobs.append((job, kwargs))


@pytest.fixture
def queue() -> FakeQueue:
    return FakeQueue()


@pytest.fixture
async def client(queue: FakeQueue) -> AsyncIterator[AsyncClient]:
    from app.core.queue import get_queue
    from app.main import app

    app.dependency_overrides[get_queue] = lambda: queue
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"
