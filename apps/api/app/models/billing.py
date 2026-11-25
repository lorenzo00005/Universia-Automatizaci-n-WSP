"""Planes, límites, suscripciones y medición de uso."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TenantMixin, TimestampMixin


class Plan(TimestampMixin, Base):
    """Plan comercial. Precios y límites viven acá, no en el código."""

    __tablename__ = "plans"

    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_public: Mapped[bool] = mapped_column(default=True)


class PlanFeature(Base):
    """Feature habilitada en un plan, con límite opcional por período.

    limit_value = None significa sin límite. period: week | month | None.
    """

    __tablename__ = "plan_features"

    plan_key: Mapped[str] = mapped_column(
        ForeignKey("plans.key", ondelete="CASCADE"), primary_key=True
    )
    feature: Mapped[str] = mapped_column(String(80), primary_key=True)
    limit_value: Mapped[int | None] = mapped_column(Integer)
    period: Mapped[str | None] = mapped_column(String(10))
    fair_use_limit: Mapped[int | None] = mapped_column(Integer)


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"


class Subscription(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "subscriptions"

    plan_key: Mapped[str] = mapped_column(ForeignKey("plans.key"))
    status: Mapped[str] = mapped_column(String(20), default=SubscriptionStatus.TRIAL)
    provider: Mapped[str | None] = mapped_column(String(20))  # mercadopago | stripe | manual
    provider_ref: Mapped[str | None] = mapped_column(String(200))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsageEvent(IdMixin, TimestampMixin, TenantMixin, Base):
    """Unidad medible: mensaje, tokens de LLM, minuto de STT, video entregado, etc."""

    __tablename__ = "usage_events"

    metric: Mapped[str] = mapped_column(String(60), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal(1))
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal(0))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ref_id: Mapped[uuid.UUID | None] = mapped_column()
    meta: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
