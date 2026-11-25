from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.db import scoped_session
from app.domains.entitlements.service import Entitlements, period_start
from app.models import UsageEvent
from tests.helpers import make_tenant


async def test_base_plan_has_no_video() -> None:
    t = await make_tenant("base")
    async with scoped_session(tenant_id=t.id) as s:
        ent = Entitlements(s)
        assert await ent.can_use(t.id, "whatsapp.atencion")
        assert not await ent.can_use(t.id, "video.edicion")
        assert await ent.quota(t.id, "video.edicion") is None


async def test_pro_weekly_video_quota() -> None:
    t = await make_tenant("pro")
    now = datetime.now(UTC)
    async with scoped_session(tenant_id=t.id) as s:
        s.add_all(
            [
                UsageEvent(tenant_id=t.id, metric="video.edicion", occurred_at=now),
                UsageEvent(tenant_id=t.id, metric="video.edicion", occurred_at=now),
                # La semana pasada no cuenta.
                UsageEvent(
                    tenant_id=t.id,
                    metric="video.edicion",
                    occurred_at=now - timedelta(days=8),
                    quantity=Decimal(3),
                ),
            ]
        )
    async with scoped_session(tenant_id=t.id) as s:
        q = await Entitlements(s).quota(t.id, "video.edicion")
    assert q is not None
    assert (q.limit, q.used, q.remaining, q.period) == (5, 2, 3, "week")


async def test_unlimited_plan_uses_fair_use_limit() -> None:
    t = await make_tenant("ilimitado")
    async with scoped_session(tenant_id=t.id) as s:
        q = await Entitlements(s).quota(t.id, "video.edicion")
    assert q is not None
    assert q.limit == 40


async def test_subscription_states() -> None:
    canceled = await make_tenant("pro", status="canceled")
    grace = await make_tenant(
        "pro", status="past_due", grace_until=datetime.now(UTC) + timedelta(days=2)
    )
    expired = await make_tenant(
        "pro", status="past_due", grace_until=datetime.now(UTC) - timedelta(days=1)
    )
    for tenant, expected in [(canceled, None), (grace, "pro"), (expired, None)]:
        async with scoped_session(tenant_id=tenant.id) as s:
            assert await Entitlements(s).plan_for(tenant.id) == expected


def test_week_starts_monday_in_tenant_timezone() -> None:
    # Lunes 30/11/2026 a las 02:00 UTC es todavía domingo 29/11 a las 23:00 en Argentina.
    now = datetime(2026, 11, 30, 2, 0, tzinfo=UTC)
    start = period_start("week", now, "America/Argentina/Buenos_Aires")
    assert start is not None
    assert start.isoformat() == "2026-11-23T00:00:00-03:00"
    assert period_start(None, now, "UTC") is None
