"""Escritura del registro de auditoría."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent


async def record(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_type: str,
    action: str,
    actor_user_id: uuid.UUID | None = None,
    tool: str | None = None,
    input: dict[str, Any] | None = None,
    output: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_user_id=actor_user_id,
        action=action,
        tool=tool,
        input=input or {},
        output=output or {},
    )
    session.add(event)
    await session.flush()
    return event
