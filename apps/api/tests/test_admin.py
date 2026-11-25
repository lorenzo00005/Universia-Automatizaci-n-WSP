from httpx import AsyncClient
from sqlalchemy import select

from app.core.db import scoped_session
from app.models import AuditEvent
from tests.conftest import FakeQueue, unique
from tests.helpers import login, make_user


async def test_admin_requires_operator(client: AsyncClient, queue: FakeQueue) -> None:
    await login(client, queue, await make_user())
    assert (await client.get("/admin/tenants")).status_code == 403


async def test_operator_creates_tenant_and_team(client: AsyncClient, queue: FakeQueue) -> None:
    await login(client, queue, await make_user(operator=True))
    slug = unique("pelu")
    r = await client.post(
        "/admin/tenants",
        json={
            "name": "Peluquería Lola",
            "slug": slug,
            "plan_key": "pro",
            "owner_email": f"{slug}@example.com",
            "owner_name": "Lola",
        },
    )
    assert r.status_code == 201, r.text
    tenant = r.json()
    assert tenant["plan_key"] == "pro"
    assert tenant["subscription_status"] == "trial"
    assert tenant["members"] == 1

    r = await client.post(
        f"/admin/tenants/{tenant['id']}/members",
        json={"email": f"emp-{slug}@example.com", "role_key": "employee"},
    )
    assert r.status_code == 201
    r = await client.post(
        f"/admin/tenants/{tenant['id']}/members",
        json={"email": f"emp-{slug}@example.com", "role_key": "employee"},
    )
    assert r.status_code == 409

    listed = (await client.get("/admin/tenants")).json()
    assert any(t["slug"] == slug and t["members"] == 2 for t in listed)

    r = await client.post(
        "/admin/tenants",
        json={"name": "Otro", "slug": slug, "owner_email": "x@example.com"},
    )
    assert r.status_code == 409

    r = await client.patch(f"/admin/tenants/{tenant['id']}", json={"training_mode": False})
    assert r.json()["training_mode"] is False

    async with scoped_session(operator=True) as s:
        actions = (
            (await s.execute(select(AuditEvent.action).where(AuditEvent.tenant_id == tenant["id"])))
            .scalars()
            .all()
        )
    assert sorted(actions) == ["member.add", "tenant.create", "tenant.update"]


async def test_plans_come_from_database(client: AsyncClient, queue: FakeQueue) -> None:
    await login(client, queue, await make_user(operator=True))
    plans = (await client.get("/admin/plans")).json()
    assert [(p["key"], p["price_usd"]) for p in plans] == [
        ("base", 50.0),
        ("pro", 100.0),
        ("ilimitado", 200.0),
    ]
