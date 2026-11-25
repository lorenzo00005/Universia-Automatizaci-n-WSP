"""Panel interno: alta y gestión manual de tenants por el equipo de Universia."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select

from app.core.db import set_context
from app.core.deps import OperatorUser, SessionDep
from app.domains.audit.service import record
from app.domains.permissions.catalog import ROLES
from app.models import Membership, Plan, Subscription, Tenant, User
from app.models.billing import SubscriptionStatus

router = APIRouter(prefix="/admin", tags=["admin"])

TRIAL_DAYS = 14


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,78}$")
    plan_key: str = "base"
    owner_email: EmailStr
    owner_name: str = ""
    owner_phone: str | None = None
    timezone: str = "America/Argentina/Buenos_Aires"


class TenantUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    training_mode: bool | None = None
    profile: dict[str, object] | None = None


class MemberCreate(BaseModel):
    email: EmailStr
    name: str = ""
    phone: str | None = None
    role_key: str = "employee"


class TenantOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    timezone: str
    training_mode: bool
    plan_key: str | None = None
    subscription_status: str | None = None
    members: int = 0


class PlanOut(BaseModel):
    key: str
    name: str
    price_usd: float


async def _get_or_create_user(
    session: SessionDep, email: str, name: str, phone: str | None
) -> User:
    result = await session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email.lower(), name=name, phone=phone)
        session.add(user)
        await session.flush()
    return user


async def _tenant_out(session: SessionDep, tenant: Tenant) -> TenantOut:
    sub = (
        await session.execute(
            select(Subscription)
            .where(Subscription.tenant_id == tenant.id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    members = (
        await session.execute(
            select(func.count()).select_from(Membership).where(Membership.tenant_id == tenant.id)
        )
    ).scalar_one()
    return TenantOut(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        timezone=tenant.timezone,
        training_mode=tenant.training_mode,
        plan_key=sub.plan_key if sub else None,
        subscription_status=sub.status if sub else None,
        members=members,
    )


@router.get("/plans", response_model=list[PlanOut])
async def list_plans(_: OperatorUser, session: SessionDep) -> list[PlanOut]:
    plans = (await session.execute(select(Plan).order_by(Plan.sort_order))).scalars()
    return [PlanOut(key=p.key, name=p.name, price_usd=float(p.price_usd)) for p in plans]


@router.get("/tenants", response_model=list[TenantOut])
async def list_tenants(_: OperatorUser, session: SessionDep) -> list[TenantOut]:
    tenants = (await session.execute(select(Tenant).order_by(Tenant.created_at.desc()))).scalars()
    return [await _tenant_out(session, t) for t in tenants]


@router.post("/tenants", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
async def create_tenant(body: TenantCreate, op: OperatorUser, session: SessionDep) -> TenantOut:
    if await session.get(Plan, body.plan_key) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ese plan no existe.")
    exists = await session.execute(select(Tenant.id).where(Tenant.slug == body.slug))
    if exists.first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya hay un negocio con ese identificador.")
    tenant = Tenant(name=body.name, slug=body.slug, timezone=body.timezone)
    session.add(tenant)
    await session.flush()
    owner = await _get_or_create_user(session, body.owner_email, body.owner_name, body.owner_phone)
    session.add(Membership(tenant_id=tenant.id, user_id=owner.id, role_key="owner"))
    session.add(
        Subscription(
            tenant_id=tenant.id,
            plan_key=body.plan_key,
            status=SubscriptionStatus.TRIAL,
            provider="manual",
            current_period_end=datetime.now(UTC) + timedelta(days=TRIAL_DAYS),
        )
    )
    await record(
        session,
        tenant_id=tenant.id,
        actor_type="operator",
        actor_user_id=op.id,
        action="tenant.create",
        input=body.model_dump(mode="json"),
    )
    return await _tenant_out(session, tenant)


@router.get("/tenants/{tenant_id}", response_model=TenantOut)
async def get_tenant(tenant_id: uuid.UUID, _: OperatorUser, session: SessionDep) -> TenantOut:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos ese negocio.")
    return await _tenant_out(session, tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantOut)
async def update_tenant(
    tenant_id: uuid.UUID, body: TenantUpdate, op: OperatorUser, session: SessionDep
) -> TenantOut:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos ese negocio.")
    changes = body.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(tenant, key, value)
    await record(
        session,
        tenant_id=tenant.id,
        actor_type="operator",
        actor_user_id=op.id,
        action="tenant.update",
        input=changes,
    )
    await session.flush()
    return await _tenant_out(session, tenant)


@router.post("/tenants/{tenant_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    tenant_id: uuid.UUID, body: MemberCreate, op: OperatorUser, session: SessionDep
) -> dict[str, str]:
    if body.role_key not in ROLES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ese rol no existe.")
    if await session.get(Tenant, tenant_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos ese negocio.")
    await set_context(session, tenant_id=tenant_id, user_id=op.id, operator=True)
    user = await _get_or_create_user(session, body.email, body.name, body.phone)
    exists = await session.execute(
        select(Membership.id).where(
            Membership.tenant_id == tenant_id, Membership.user_id == user.id
        )
    )
    if exists.first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa persona ya está en el equipo.")
    session.add(Membership(tenant_id=tenant_id, user_id=user.id, role_key=body.role_key))
    await record(
        session,
        tenant_id=tenant_id,
        actor_type="operator",
        actor_user_id=op.id,
        action="member.add",
        input=body.model_dump(mode="json"),
    )
    return {"user_id": str(user.id)}
