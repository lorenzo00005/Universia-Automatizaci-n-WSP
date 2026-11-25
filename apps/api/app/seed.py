"""Datos de prueba para desarrollo: `make seed`.

Crea un operador interno (SEED_OPERATOR_EMAIL) y un negocio de ejemplo con dueño y empleado.
Es idempotente: si ya existen, no duplica nada.
"""

import asyncio
import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import scoped_session
from app.models import Membership, Subscription, Tenant, User


async def _user(session: AsyncSession, email: str, name: str, *, operator: bool = False) -> User:
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        user = User(email=email, name=name, is_operator=operator)
        session.add(user)
        await session.flush()
    return user


async def main() -> None:
    operator_email = os.environ.get("SEED_OPERATOR_EMAIL", "operador@example.com")
    async with scoped_session(operator=True) as session:
        await _user(session, operator_email, "Operador", operator=True)
        tenant = (
            await session.execute(select(Tenant).where(Tenant.slug == "negocio-demo"))
        ).scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(
                name="Peluquería Demo",
                slug="negocio-demo",
                profile={"rubro": "peluquería", "horarios": "Lun a Sáb de 9 a 19"},
            )
            session.add(tenant)
            await session.flush()
            owner = await _user(session, "duenio@example.com", "Dueña Demo")
            employee = await _user(session, "empleado@example.com", "Empleado Demo")
            session.add_all(
                [
                    Membership(tenant_id=tenant.id, user_id=owner.id, role_key="owner"),
                    Membership(tenant_id=tenant.id, user_id=employee.id, role_key="employee"),
                    Subscription(
                        tenant_id=tenant.id,
                        plan_key="pro",
                        status="trial",
                        provider="manual",
                        current_period_end=datetime.now(UTC) + timedelta(days=14),
                    ),
                ]
            )
    print(f"Listo. Entrá al panel con {operator_email} (el mail llega a Mailpit).")


if __name__ == "__main__":
    asyncio.run(main())
