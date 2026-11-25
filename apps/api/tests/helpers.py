"""Helpers para armar datos y loguearse en los tests."""

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient

from app.core.db import scoped_session
from app.models import Membership, Subscription, Tenant, User
from tests.conftest import FakeQueue, unique


async def make_user(*, operator: bool = False, name: str = "Test") -> User:
    async with scoped_session(operator=True) as s:
        user = User(email=f"{unique('u')}@example.com", name=name, is_operator=operator)
        s.add(user)
    return user


async def make_tenant(
    plan: str = "base", status: str = "trial", grace_until: datetime | None = None
) -> Tenant:
    async with scoped_session(operator=True) as s:
        tenant = Tenant(name="Negocio de test", slug=unique("t"))
        s.add(tenant)
        await s.flush()
        s.add(
            Subscription(
                tenant_id=tenant.id,
                plan_key=plan,
                status=status,
                grace_until=grace_until,
                current_period_end=datetime.now(UTC) + timedelta(days=14),
            )
        )
    return tenant


async def add_member(tenant_id: uuid.UUID, user_id: uuid.UUID, role: str, **kw: object) -> None:
    async with scoped_session(operator=True) as s:
        s.add(Membership(tenant_id=tenant_id, user_id=user_id, role_key=role, **kw))


async def login(client: AsyncClient, queue: FakeQueue, user: User) -> None:
    r = await client.post("/auth/magic-link", json={"email": user.email})
    assert r.status_code == 202
    job, kwargs = queue.jobs[-1]
    assert job == "send_magic_link"
    token = parse_qs(urlparse(kwargs["link"]).query)["token"][0]
    r = await client.post("/auth/verify", json={"token": token})
    assert r.status_code == 200, r.text
