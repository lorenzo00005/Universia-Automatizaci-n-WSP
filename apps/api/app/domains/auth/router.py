"""Login del dashboard por magic link (email). El OTP por WhatsApp llega en la Fase 1."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update

from app.core.config import get_settings
from app.core.crypto import hash_token, new_token
from app.core.deps import CurrentUser, SessionDep
from app.core.queue import JobQueue, get_queue
from app.domains.permissions.service import effective_permissions
from app.models import AuthToken, Membership, Tenant, User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"])


class MagicLinkIn(BaseModel):
    email: EmailStr


class VerifyIn(BaseModel):
    token: str


class TenantOut(BaseModel):
    id: str
    name: str
    role: str
    permissions: list[str]


class MeOut(BaseModel):
    id: str
    email: str | None
    name: str
    is_operator: bool
    tenants: list[TenantOut]


@router.post("/magic-link", status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(
    body: MagicLinkIn, session: SessionDep, queue: JobQueue = Depends(get_queue)
) -> dict[str, bool]:
    """Siempre responde 202 para no revelar qué emails existen."""
    settings = get_settings()
    result = await session.execute(
        select(User).where(User.email == body.email.lower(), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is not None:
        token = new_token()
        session.add(
            AuthToken(
                user_id=user.id,
                kind="magic_link",
                token_hash=hash_token(token),
                expires_at=datetime.now(UTC) + timedelta(minutes=settings.magic_link_ttl_minutes),
            )
        )
        await session.flush()
        link = f"{settings.public_url}/auth/verify?token={token}"
        await queue.enqueue("send_magic_link", email=user.email, name=user.name, link=link)
    return {"ok": True}


@router.post("/verify")
async def verify(body: VerifyIn, response: Response, session: SessionDep) -> dict[str, bool]:
    settings = get_settings()
    now = datetime.now(UTC)
    result = await session.execute(
        update(AuthToken)
        .where(
            AuthToken.token_hash == hash_token(body.token),
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > now,
        )
        .values(used_at=now)
        .returning(AuthToken.user_id)
    )
    user_id = result.scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El link venció o ya se usó. Pedí otro.")
    token = new_token()
    session.add(
        UserSession(
            user_id=user_id,
            token_hash=hash_token(token),
            expires_at=now + timedelta(hours=settings.session_ttl_hours),
        )
    )
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )
    return {"ok": True}


@router.post("/logout")
async def logout(request: Request, response: Response, session: SessionDep) -> dict[str, bool]:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await session.execute(
            update(UserSession)
            .where(UserSession.token_hash == hash_token(token))
            .values(revoked_at=datetime.now(UTC))
        )
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"ok": True}


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser, session: SessionDep) -> MeOut:
    # RLS deja ver sólo las membresías del propio usuario (app.user_id).
    rows = await session.execute(
        select(Membership, Tenant)
        .join(Tenant, Tenant.id == Membership.tenant_id)
        .where(Membership.user_id == user.id)
        .order_by(Tenant.name)
    )
    tenants = [
        TenantOut(
            id=str(t.id),
            name=t.name,
            role=m.role_key,
            permissions=sorted(await effective_permissions(session, m)),
        )
        for m, t in rows.all()
    ]
    return MeOut(
        id=str(user.id),
        email=user.email,
        name=user.name,
        is_operator=user.is_operator,
        tenants=tenants,
    )
