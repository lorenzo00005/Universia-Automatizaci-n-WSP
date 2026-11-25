from httpx import AsyncClient

from app.core.db import scoped_session
from app.domains.permissions.service import effective_permissions, get_membership
from tests.conftest import FakeQueue
from tests.helpers import add_member, login, make_tenant, make_user


async def test_employee_cannot_see_audit_or_finances(client: AsyncClient, queue: FakeQueue) -> None:
    tenant = await make_tenant()
    employee = await make_user()
    await add_member(tenant.id, employee.id, "employee")
    await login(client, queue, employee)

    assert (await client.get(f"/tenants/{tenant.id}/audit")).status_code == 403
    perms = (await client.get("/auth/me")).json()["tenants"][0]["permissions"]
    assert "finanzas.ver" not in perms
    assert "agenda.gestionar" in perms


async def test_owner_can_see_audit(client: AsyncClient, queue: FakeQueue) -> None:
    tenant = await make_tenant()
    owner = await make_user()
    await add_member(tenant.id, owner.id, "owner")
    await login(client, queue, owner)
    assert (await client.get(f"/tenants/{tenant.id}/audit")).status_code == 200


async def test_extra_and_denied_permissions() -> None:
    tenant = await make_tenant()
    user = await make_user()
    await add_member(
        tenant.id,
        user.id,
        "employee",
        extra_permissions=["finanzas.ver"],
        denied_permissions=["crm.gestionar"],
    )
    async with scoped_session(tenant_id=tenant.id) as s:
        m = await get_membership(s, tenant.id, user.id)
        assert m is not None
        perms = await effective_permissions(s, m)
    assert "finanzas.ver" in perms
    assert "crm.gestionar" not in perms
    assert "crm.ver" in perms
