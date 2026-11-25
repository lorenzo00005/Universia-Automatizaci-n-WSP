from sqlalchemy import select, text

from app.core.db import scoped_session
from app.models import Channel
from app.worker.main import build_magic_link_email
from tests.conftest import unique
from tests.helpers import make_tenant


async def test_channel_token_is_encrypted_at_rest() -> None:
    t = await make_tenant()
    external = unique("pnid")
    async with scoped_session(tenant_id=t.id) as s:
        s.add(
            Channel(
                tenant_id=t.id,
                kind="whatsapp",
                purpose="business",
                external_id=external,
                access_token="EAAG-secreto",
            )
        )
    async with scoped_session(tenant_id=t.id) as s:
        raw = (
            await s.execute(
                text("select access_token from channels where external_id = :e"),
                {"e": external},
            )
        ).scalar_one()
        channel = (
            await s.execute(select(Channel).where(Channel.external_id == external))
        ).scalar_one()
    assert raw != "EAAG-secreto"
    assert channel.access_token == "EAAG-secreto"


def test_magic_link_email_is_in_spanish() -> None:
    msg = build_magic_link_email("ana@example.com", "Ana", "http://localhost/auth/verify?token=x")
    body = msg.get_content()
    assert "Hola Ana" in body
    assert "Entrá al panel" in body
    assert msg["Subject"] == "Tu link para entrar a Universia"
