from httpx import AsyncClient

from tests.conftest import FakeQueue
from tests.helpers import add_member, login, make_tenant, make_user


async def test_magic_link_unknown_email_does_not_leak(
    client: AsyncClient, queue: FakeQueue
) -> None:
    r = await client.post("/auth/magic-link", json={"email": "nadie@example.com"})
    assert r.status_code == 202
    assert queue.jobs == []


async def test_magic_link_full_flow(client: AsyncClient, queue: FakeQueue) -> None:
    user = await make_user(name="Ana")
    tenant = await make_tenant()
    await add_member(tenant.id, user.id, "owner")

    assert (await client.get("/auth/me")).status_code == 401
    await login(client, queue, user)

    me = (await client.get("/auth/me")).json()
    assert me["email"] == user.email
    assert [t["id"] for t in me["tenants"]] == [str(tenant.id)]
    assert me["tenants"][0]["role"] == "owner"
    assert "facturacion.gestionar" in me["tenants"][0]["permissions"]

    # El link es de un solo uso.
    link = queue.jobs[-1][1]["link"]
    token = link.split("token=")[1]
    assert (await client.post("/auth/verify", json={"token": token})).status_code == 400

    assert (await client.post("/auth/logout")).status_code == 200
    assert (await client.get("/auth/me")).status_code == 401


async def test_invalid_token(client: AsyncClient) -> None:
    r = await client.post("/auth/verify", json={"token": "cualquiera"})
    assert r.status_code == 400
