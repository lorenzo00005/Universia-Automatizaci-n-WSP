"""Servicio de entitlements: qué puede usar un tenant y cuánto le queda.

Responde "¿este tenant puede usar X?" y "¿cuánto le queda de Y en este período?"
leyendo planes y límites de la base (`plans`, `plan_features`) y el uso de `usage_events`.
La sesión tiene que tener fijado el contexto del tenant (RLS).
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PlanFeature, Subscription, Tenant, UsageEvent
from app.models.billing import SubscriptionStatus

USABLE_STATUSES = {SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE}


@dataclass(frozen=True)
class Quota:
    feature: str
    limit: int | None  # None = sin límite
    used: int
    period: str | None

    @property
    def remaining(self) -> int | None:
        return None if self.limit is None else max(self.limit - self.used, 0)


def period_start(period: str | None, now: datetime, tz: str) -> datetime | None:
    """Inicio del período en la zona horaria del tenant (semana ISO: lunes 00:00)."""
    if period is None:
        return None
    local = now.astimezone(ZoneInfo(tz))
    midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return midnight - timedelta(days=local.weekday())
    if period == "month":
        return midnight.replace(day=1)
    raise ValueError(f"Período desconocido: {period}")


class Entitlements:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def plan_for(self, tenant_id: uuid.UUID, now: datetime | None = None) -> str | None:
        now = now or datetime.now(UTC)
        result = await self.session.execute(
            select(Subscription)
            .where(Subscription.tenant_id == tenant_id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return None
        if sub.status in USABLE_STATUSES:
            return sub.plan_key
        # Morosa pero dentro del período de gracia: sigue funcionando.
        if sub.status == SubscriptionStatus.PAST_DUE and sub.grace_until and sub.grace_until > now:
            return sub.plan_key
        return None

    async def _feature(self, tenant_id: uuid.UUID, feature: str) -> PlanFeature | None:
        plan = await self.plan_for(tenant_id)
        if plan is None:
            return None
        return await self.session.get(PlanFeature, (plan, feature))

    async def can_use(self, tenant_id: uuid.UUID, feature: str) -> bool:
        return await self._feature(tenant_id, feature) is not None

    async def quota(
        self, tenant_id: uuid.UUID, feature: str, now: datetime | None = None
    ) -> Quota | None:
        """Cupo del período. None si el plan no incluye la feature."""
        now = now or datetime.now(UTC)
        pf = await self._feature(tenant_id, feature)
        if pf is None:
            return None
        limit = pf.limit_value if pf.limit_value is not None else pf.fair_use_limit
        start = None
        if pf.period:
            tenant = await self.session.get(Tenant, tenant_id)
            tz = tenant.timezone if tenant else "UTC"
            start = period_start(pf.period, now, tz)
        query = select(func.coalesce(func.sum(UsageEvent.quantity), Decimal(0))).where(
            UsageEvent.tenant_id == tenant_id, UsageEvent.metric == feature
        )
        if start is not None:
            query = query.where(UsageEvent.occurred_at >= start, UsageEvent.occurred_at <= now)
        used = int((await self.session.execute(query)).scalar_one())
        return Quota(feature=feature, limit=limit, used=used, period=pf.period)
