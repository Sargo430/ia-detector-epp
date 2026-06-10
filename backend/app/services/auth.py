"""
Auth service — login, register, refresh, password change.
All writes happen inside the tenant-scoped session passed in from deps.
"""
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.user import UserRegister, LoginRequest, TokenResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.config import settings


# ── Tenant lookup (public schema) ─────────────────────────────────────────────
async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Tenant | None:
    result = await db.execute(
        select(Tenant).where(Tenant.slug == slug, Tenant.is_active == True)
    )
    return result.scalar_one_or_none()


# ── User CRUD ─────────────────────────────────────────────────────────────────
async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: UserRegister,
    is_superuser: bool = False,
) -> User:
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise ValueError("Email already registered in this tenant")

    user = User(
        tenant_id=tenant_id,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def list_users(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[User]]:
    q = select(User).where(User.tenant_id == tenant_id)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    users = await db.execute(
        q.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total or 0, list(users.scalars().all())


# ── Auth operations ───────────────────────────────────────────────────────────
async def authenticate(
    db: AsyncSession, email: str, password: str
) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def build_token_response(user: User, tenant_slug: str) -> TokenResponse:
    extra = {"role": user.role, "email": user.email}
    access = create_access_token(user.id, tenant_slug, extra)
    refresh = create_refresh_token(user.id, tenant_slug)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_tokens(
    db: AsyncSession, refresh_token: str
) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except ValueError as e:
        raise ValueError(f"Invalid refresh token: {e}")

    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")

    user_id = uuid.UUID(payload["sub"])
    tenant_slug = payload["tenant"]

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    return build_token_response(user, tenant_slug)


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise ValueError("Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    await db.flush()
