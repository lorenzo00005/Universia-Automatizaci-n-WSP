"""Motor y sesiones de base de datos con contexto de tenant para RLS.

Cada transacción fija `app.tenant_id` (y opcionalmente `app.user_id` / `app.operator`)
con `set_config(..., true)`, que dura sólo hasta el fin de la transacción. Las políticas
de Row Level Security de Postgres usan esos valores, así que una consulta sin contexto
no ve filas de ningún tenant.
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def set_context(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    operator: bool = False,
) -> None:
    await session.execute(
        text(
            "select set_config('app.tenant_id', :t, true),"
            " set_config('app.user_id', :u, true),"
            " set_config('app.operator', :o, true)"
        ),
        {
            "t": str(tenant_id) if tenant_id else "",
            "u": str(user_id) if user_id else "",
            "o": "on" if operator else "off",
        },
    )


@asynccontextmanager
async def scoped_session(
    *,
    tenant_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    operator: bool = False,
) -> AsyncIterator[AsyncSession]:
    """Sesión transaccional con el contexto de RLS ya fijado. Hace commit al salir."""
    async with get_sessionmaker()() as session, session.begin():
        await set_context(session, tenant_id=tenant_id, user_id=user_id, operator=operator)
        yield session


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: sesión sin contexto de tenant (sólo tablas globales)."""
    async with scoped_session() as session:
        yield session
