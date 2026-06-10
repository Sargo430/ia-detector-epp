"""
Multi-tenant schema routing.
Each tenant gets its own PostgreSQL schema: tenant_<slug>
The public schema holds the tenants registry only.
"""
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def set_search_path(db: AsyncSession, schema: str) -> None:
    """Switch the session's search_path to tenant schema."""
    await db.execute(text(f"SET search_path TO {schema}, public"))


async def create_tenant_schema(db: AsyncSession, schema: str) -> None:
    """Provision a new schema + all tables for a tenant."""
    await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
    # Alembic runs migrations per-schema; here we just create the shell
    await db.commit()


async def drop_tenant_schema(db: AsyncSession, schema: str) -> None:
    """Tear down a tenant schema (use with caution!)."""
    await db.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
    await db.commit()


def tenant_schema_name(slug: str) -> str:
    return f"tenant_{slug}"


@asynccontextmanager
async def tenant_session(db: AsyncSession, slug: str):
    """Context manager that switches search_path for the duration."""
    schema = tenant_schema_name(slug)
    await set_search_path(db, schema)
    try:
        yield db
    finally:
        await set_search_path(db, "public")
