"""Endpoints del negocio para sus miembros, filtrados por permisos y RLS."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.core.deps import SessionDep, TenantAccess, require_permission
from app.domains.entitlements.service import Entitlements
from app.domains.permissions.catalog import Perm
from app.models import AuditEvent, PlanFeature

router = APIRouter(prefix="/tenants/{tenant_id}", tags=["tenants"])

Member = Annotated[TenantAccess, Depends(require_permission())]
Auditor = Annotated[TenantAccess, Depends(require_permission(Perm.AUDITORIA_VER))]


class FeatureOut(BaseModel):
    feature: str
    limit: int | None
    used: int
    remaining: int | None
    period: str | None


class EntitlementsOut(BaseModel):
    plan_key: str | None
    features: list[FeatureOut]


class AuditOut(BaseModel):
    action: str
    actor_type: str
    tool: str | None
    created_at: str


@router.get("/entitlements", response_model=EntitlementsOut)
async def entitlements(access: Member, session: SessionDep) -> EntitlementsOut:
    ent = Entitlements(session)
    plan = await ent.plan_for(access.tenant_id)
    features: list[FeatureOut] = []
    if plan:
        keys = (
            await session.execute(
                select(PlanFeature.feature)
                .where(PlanFeature.plan_key == plan)
                .order_by(PlanFeature.feature)
            )
        ).scalars()
        for key in keys:
            q = await ent.quota(access.tenant_id, key)
            if q:
                features.append(
                    FeatureOut(
                        feature=key,
                        limit=q.limit,
                        used=q.used,
                        remaining=q.remaining,
                        period=q.period,
                    )
                )
    return EntitlementsOut(plan_key=plan, features=features)


@router.get("/audit", response_model=list[AuditOut])
async def audit(access: Auditor, session: SessionDep) -> list[AuditOut]:
    rows = (
        await session.execute(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == access.tenant_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
        )
    ).scalars()
    return [
        AuditOut(
            action=e.action,
            actor_type=e.actor_type,
            tool=e.tool,
            created_at=e.created_at.isoformat(),
        )
        for e in rows
    ]
