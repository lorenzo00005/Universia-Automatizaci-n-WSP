"""Canales de mensajería (WhatsApp hoy; Instagram, email, webchat después)."""

from enum import StrEnum

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.crypto import EncryptedString
from app.models.base import Base, IdMixin, TenantMixin, TimestampMixin


class ChannelKind(StrEnum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    WEBCHAT = "webchat"
    SIMULATOR = "simulator"


class ChannelPurpose(StrEnum):
    INTERNAL = "internal"  # línea del dueño y su equipo con el asistente
    BUSINESS = "business"  # línea del negocio con sus clientes


class Channel(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "channels"
    __table_args__ = (UniqueConstraint("kind", "external_id"),)

    kind: Mapped[str] = mapped_column(String(20))
    purpose: Mapped[str] = mapped_column(String(20))
    # En WhatsApp: phone_number_id de Meta. Sirve para rutear el webhook al tenant.
    external_id: Mapped[str] = mapped_column(String(120))
    display_phone: Mapped[str | None] = mapped_column(String(32))
    access_token: Mapped[str | None] = mapped_column(EncryptedString(2000))
    config: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MessageTemplate(IdMixin, TimestampMixin, TenantMixin, Base):
    """Plantillas aprobadas por Meta para escribir fuera de la ventana de 24 h."""

    __tablename__ = "message_templates"
    __table_args__ = (UniqueConstraint("tenant_id", "name", "language"),)

    name: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(10), default="es_AR")
    category: Mapped[str] = mapped_column(String(30))  # utility | marketing | authentication
    status: Mapped[str] = mapped_column(String(20), default="draft")
    components: Mapped[list[dict[str, object]]] = mapped_column(JSONB, default=list)
