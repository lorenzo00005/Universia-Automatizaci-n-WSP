"""Resolución de permisos efectivos de un usuario dentro de un tenant."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, RolePermission


async def get_membership(
    session: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> Membership | None:
    result = await session.execute(
        select(Membership).where(Membership.tenant_id == tenant_id, Membership.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def effective_permissions(session: AsyncSession, membership: Membership) -> set[str]:
    rows = await session.execute(
        select(RolePermission.permission).where(RolePermission.role_key == membership.role_key)
    )
    perms = set(rows.scalars())
    perms |= set(membership.extra_permissions or [])
    perms -= set(membership.denied_permissions or [])
    return perms
