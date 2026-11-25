"""Registro auditable de cada acción (del agente, de usuarios y de operadores)."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TenantMixin, TimestampMixin


class AuditEvent(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "audit_events"

    actor_type: Mapped[str] = mapped_column(String(20))  # user | agent | operator | system
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(120), index=True)
    tool: Mapped[str | None] = mapped_column(String(80))
    input: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    output: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    approval_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("approvals.id", ondelete="SET NULL")
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL")
    )
