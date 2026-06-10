"""
FastAPI dependency injectors.
Provides: current user (full ORM object), tenant-scoped DB session,
role guards, public DB for auth endpoints.
"""
import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.db.tenant import tenant_session
from app.models.user import User

bearer = HTTPBearer()


# ── Token decoding ────────────────────────────────────────────────────────────
async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")
    return payload


# ── Public DB (search_path = public) — used only by auth endpoints ─────────────
async def get_public_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    yield db


# ── Tenant-scoped DB ──────────────────────────────────────────────────────────
async def get_tenant_db(
    payload: Annotated[dict, Depends(get_token_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncSession:
    slug = payload.get("tenant")
    if not slug:
        raise HTTPException(status_code=400, detail="Token missing tenant claim")
    async with tenant_session(db, slug) as scoped_db:
        yield scoped_db


# ── Resolve full User ORM object ──────────────────────────────────────────────
async def get_current_user(
    payload: Annotated[dict, Depends(get_token_payload)],
    db: Annotated[AsyncSession, Depends(get_tenant_db)],
) -> User:
    from app.services.auth import get_user_by_id
    user_id = uuid.UUID(payload["sub"])
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


# ── Role guards ───────────────────────────────────────────────────────────────
def require_roles(*roles: str):
    """Factory: returns a dependency that enforces one of the given roles."""
    async def _guard(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {' | '.join(roles)}",
            )
        return user
    return _guard


# ── Typed aliases ─────────────────────────────────────────────────────────────
TenantDB    = Annotated[AsyncSession, Depends(get_tenant_db)]
PublicDB    = Annotated[AsyncSession, Depends(get_public_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser   = Annotated[User, Depends(require_roles("admin"))]
OperatorUser = Annotated[User, Depends(require_roles("admin", "operator"))]
