"""Contactos (clientes y leads), conversaciones y mensajes."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TenantMixin, TimestampMixin


class LeadStage(StrEnum):
    NEW = "nuevo"
    CONTACTED = "contactado"
    REPLIED = "respondio"
    WON = "cerrado"
    LOST = "perdido"


class Contact(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("tenant_id", "phone"),)

    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))
    name: Mapped[str] = mapped_column(String(200), default="")
    is_lead: Mapped[bool] = mapped_column(default=False)
    stage: Mapped[str | None] = mapped_column(String(20))
    opted_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str] = mapped_column(Text, default="")
    attributes: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)


class ConversationStatus(StrEnum):
    BOT = "bot"  # atiende el asistente
    HUMAN = "human"  # el dueño tomó la conversación (handoff)
    CLOSED = "closed"


class Conversation(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "conversations"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), default=ConversationStatus.BOT)
    handled_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    # Fin de la ventana de 24 h para mensajes libres (después sólo plantillas).
    service_window_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Message(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        # Idempotencia del webhook: el mismo message_id de Meta no se procesa dos veces.
        UniqueConstraint("tenant_id", "external_id"),
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE")
    )
    external_id: Mapped[str | None] = mapped_column(String(200))
    direction: Mapped[str] = mapped_column(String(10))  # in | out
    sender: Mapped[str] = mapped_column(String(20))  # contact | user | assistant | system
    kind: Mapped[str] = mapped_column(String(20), default="text")
    body: Mapped[str] = mapped_column(Text, default="")
    media_url: Mapped[str | None] = mapped_column(String(1000))
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="received")
