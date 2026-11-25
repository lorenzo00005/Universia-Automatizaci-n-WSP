"""Dependencias de FastAPI: usuario actual, operador, acceso a tenant con permisos."""

import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import hash_token
from app.core.db import get_session, set_context
from app.domains.permissions.service import effective_permissions, get_membership
from app.models import Membership, User, UserSession

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def current_user(request: Request, session: SessionDep) -> User:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tenés que iniciar sesión.")
    result = await session.execute(
        select(User)
        .join(UserSession, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC),
            User.is_active.is_(True),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tu sesión venció. Volvé a entrar.")
    await set_context(session, user_id=user.id)
    return user


CurrentUser = Annotated[User, Depends(current_user)]


async def operator_user(user: CurrentUser, session: SessionDep) -> User:
    if not user.is_operator:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sólo para el equipo interno.")
    await set_context(session, user_id=user.id, operator=True)
    return user


OperatorUser = Annotated[User, Depends(operator_user)]


@dataclass
class TenantAccess:
    tenant_id: uuid.UUID
    user: User
    membership: Membership
    permissions: set[str]


def require_permission(
    permission: str | None = None,
) -> Callable[..., Coroutine[Any, Any, TenantAccess]]:
    """Valida que el usuario sea miembro del tenant y tenga el permiso pedido.

    Fija el contexto de RLS del tenant en la sesión para el resto del request.
    """

    async def dependency(
        tenant_id: uuid.UUID, user: CurrentUser, session: SessionDep
    ) -> TenantAccess:
        await set_context(session, tenant_id=tenant_id, user_id=user.id)
        membership = await get_membership(session, tenant_id, user.id)
        if membership is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos ese negocio.")
        perms = await effective_permissions(session, membership)
        if permission and permission not in perms:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tenés permiso para esto.")
        return TenantAccess(tenant_id, user, membership, perms)

    return dependency
