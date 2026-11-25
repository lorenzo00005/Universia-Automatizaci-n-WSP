"""Tenants, usuarios, membresías, roles y permisos."""

import uuid
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TenantMixin, TimestampMixin


class TenantStatus(StrEnum):
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Tenant(IdMixin, TimestampMixin, Base):
    """Un negocio cliente. Tabla global (sin RLS): sólo la tocan operadores y el sistema."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    status: Mapped[str] = mapped_column(String(20), default=TenantStatus.ONBOARDING)
    timezone: Mapped[str] = mapped_column(String(64), default="America/Argentina/Buenos_Aires")
    locale: Mapped[str] = mapped_column(String(10), default="es-AR")
    # Perfil del negocio: rubro, horarios, políticas, tono de marca, etc.
    profile: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    # Modo entrenamiento: el agente propone y el dueño aprueba (primera semana).
    training_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    monthly_llm_budget_usd: Mapped[float] = mapped_column(default=15.0)


class User(IdMixin, TimestampMixin, Base):
    """Persona que usa el sistema. Puede pertenecer a varios tenants."""

    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    is_operator: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Role(Base):
    """Roles del sistema (owner, admin, employee). Tabla global."""

    __tablename__ = "roles"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_key: Mapped[str] = mapped_column(
        ForeignKey("roles.key", ondelete="CASCADE"), primary_key=True
    )
    permission: Mapped[str] = mapped_column(String(80), primary_key=True)


class Membership(IdMixin, TimestampMixin, TenantMixin, Base):
    """Usuario dentro de un tenant con un rol y permisos extra opcionales."""

    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role_key: Mapped[str] = mapped_column(ForeignKey("roles.key"))
    extra_permissions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    denied_permissions: Mapped[list[str]] = mapped_column(JSONB, default=list)
