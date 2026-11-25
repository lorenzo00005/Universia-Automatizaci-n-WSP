"""Aislamiento entre tenants: RLS en Postgres y chequeos de membresía en la API."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError

from app.core.db import scoped_session
from app.models import Contact
from tests.conftest import FakeQueue
from tests.helpers import add_member, login, make_tenant, make_user


async def test_rls_only_shows_own_tenant_rows() -> None:
    a = await make_tenant()
    b = await make_tenant()
    async with scoped_session(tenant_id=a.id) as s:
        s.add(Contact(tenant_id=a.id, phone="+5491100000001", name="Cliente A"))
    async with scoped_session(tenant_id=b.id) as s:
        s.add(Contact(tenant_id=b.id, phone="+5491100000002", name="Cliente B"))

    async with scoped_session(tenant_id=a.id) as s:
        # Aunque la consulta no filtre por tenant, la base sólo devuelve las filas de A.
        names = (await s.execute(select(Contact.name))).scalars().all()
    assert names == ["Cliente A"]

    async with scoped_session() as s:
        assert (await s.execute(select(Contact))).scalars().all() == []


async def test_rls_blocks_writes_into_another_tenant() -> None:
    a = await make_tenant()
    b = await make_tenant()
    with pytest.raises(DBAPIError):
        async with scoped_session(tenant_id=a.id) as s:
            s.add(Contact(tenant_id=b.id, phone="+5491100000003", name="Intruso"))


async def test_member_cannot_read_other_tenant(client: AsyncClient, queue: FakeQueue) -> None:
    user = await make_user()
    mine = await make_tenant()
    other = await make_tenant()
    await add_member(mine.id, user.id, "owner")
    await login(client, queue, user)

    assert (await client.get(f"/tenants/{mine.id}/entitlements")).status_code == 200
    assert (await client.get(f"/tenants/{other.id}/entitlements")).status_code == 404
    assert (await client.get(f"/tenants/{other.id}/audit")).status_code == 404

    me = (await client.get("/auth/me")).json()
    assert [t["id"] for t in me["tenants"]] == [str(mine.id)]
