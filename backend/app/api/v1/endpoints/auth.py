"""
Auth endpoints — login, refresh, register, me, password change.

Public routes  (no token needed): /login, /refresh
Protected routes (token required): /me, /me/password, /register (admin only)
"""
import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    TenantDB, PublicDB, CurrentUser, AdminUser,
    get_token_payload, get_public_db,
)
from app.schemas.user import (
    LoginRequest, TokenResponse, RefreshRequest,
    UserRegister, UserUpdate, UserResponse,
    UserListResponse, PasswordChange,
)
from app.services import auth as svc
from app.db.tenant import tenant_session

router = APIRouter(prefix="/auth", tags=["auth"])


# ── POST /auth/login ──────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: PublicDB):
    """
    Authenticate with email + password + tenant_slug.
    Returns access + refresh tokens.
    """
    # 1. Verify tenant exists in public schema
    tenant = await svc.get_tenant_by_slug(db, body.tenant_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found or inactive")

    # 2. Switch to tenant schema and authenticate
    async with tenant_session(db, tenant.slug) as tenant_db:
        user = await svc.authenticate(tenant_db, body.email, body.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return svc.build_token_response(user, tenant.slug)


# ── POST /auth/refresh ────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: PublicDB):
    """Exchange a valid refresh token for a new token pair."""
    try:
        # Decode to get tenant slug, then switch schema
        from app.core.security import decode_token
        payload = decode_token(body.refresh_token)
        tenant_slug = payload.get("tenant")
        if not tenant_slug:
            raise ValueError("Token missing tenant claim")

        async with tenant_session(db, tenant_slug) as tenant_db:
            return await svc.refresh_tokens(tenant_db, body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# ── GET /auth/me ──────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    """Return the authenticated user's profile."""
    return current_user


# ── PATCH /auth/me ────────────────────────────────────────────────────────────
@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: CurrentUser,
    db: TenantDB,
):
    """Update own profile (full_name only — role change requires admin)."""
    if body.role and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cannot change own role")

    patch = body.model_dump(exclude_unset=True)
    for field, value in patch.items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


# ── POST /auth/me/password ────────────────────────────────────────────────────
@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChange,
    current_user: CurrentUser,
    db: TenantDB,
):
    """Change own password. Requires current password for confirmation."""
    try:
        await svc.change_password(db, current_user, body.current_password, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── POST /auth/register ───────────────────────────────────────────────────────
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: UserRegister,
    admin: AdminUser,       # ← only admins can invite users
    db: TenantDB,
):
    """
    Create a new user inside the current tenant.
    Only accessible to admins.
    """
    try:
        user = await svc.create_user(db, admin.tenant_id, body)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return user


# ── GET /auth/users ───────────────────────────────────────────────────────────
@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin: AdminUser,
    db: TenantDB,
    page: int = 1,
    page_size: int = 20,
):
    """List all users in the tenant. Admin only."""
    total, users = await svc.list_users(db, admin.tenant_id, page, page_size)
    return UserListResponse(total=total, page=page, page_size=page_size, items=users)


# ── PATCH /auth/users/{user_id} ───────────────────────────────────────────────
@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    admin: AdminUser,
    db: TenantDB,
):
    """Update another user's role or active status. Admin only."""
    user = await svc.get_user_by_id(db, user_id)
    if not user or user.tenant_id != admin.tenant_id:
        raise HTTPException(status_code=404, detail="User not found")

    patch = body.model_dump(exclude_unset=True)
    for field, value in patch.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


# ── DELETE /auth/users/{user_id} ──────────────────────────────────────────────
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    admin: AdminUser,
    db: TenantDB,
):
    """Soft-delete: deactivates the user. Admin only."""
    user = await svc.get_user_by_id(db, user_id)
    if not user or user.tenant_id != admin.tenant_id:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False
    await db.flush()
