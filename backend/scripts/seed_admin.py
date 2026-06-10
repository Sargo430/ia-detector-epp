"""
CLI: python scripts/seed_admin.py <tenant_slug> <email> <password>
Creates the first admin user for a tenant.
"""
import asyncio, sys
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.db.tenant import tenant_session, tenant_schema_name
from app.services.auth import get_tenant_by_slug, create_user, get_user_by_email
from app.schemas.user import UserRegister


async def main(slug: str, email: str, password: str):
    async with AsyncSessionLocal() as db:
        tenant = await get_tenant_by_slug(db, slug)
        if not tenant:
            print(f"❌  Tenant '{slug}' not found. Run create_tenant.py first.")
            sys.exit(1)

        async with tenant_session(db, slug) as tdb:
            existing = await get_user_by_email(tdb, email)
            if existing:
                print(f"⚠️   User '{email}' already exists in tenant '{slug}'")
                return

            user = await create_user(
                tdb,
                tenant.id,
                UserRegister(email=email, password=password, role="admin"),
                is_superuser=True,
            )
            await tdb.commit()
            print(f"✅  Admin '{email}' created in tenant '{slug}' (id: {user.id})")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: seed_admin.py <tenant_slug> <email> <password>")
        sys.exit(1)
    asyncio.run(main(*sys.argv[1:]))
