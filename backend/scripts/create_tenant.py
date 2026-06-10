"""
CLI: python scripts/create_tenant.py <slug> <name> <email>

Provisiona un nuevo tenant:
  1. Inserta en public.tenants
  2. Crea el schema PostgreSQL
  3. Corre las migraciones de tenant automáticamente
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.db.tenant import create_tenant_schema, tenant_schema_name


async def provision_tenant(slug: str, name: str, email: str) -> str:
    schema = tenant_schema_name(slug)

    async with AsyncSessionLocal() as db:
        # 1. Insertar en public.tenants
        await db.execute(
            text("""
                INSERT INTO tenants (name, slug, schema_name, contact_email)
                VALUES (:name, :slug, :schema, :email)
                ON CONFLICT (slug) DO NOTHING
            """),
            {"name": name, "slug": slug, "schema": schema, "email": email},
        )
        # 2. Crear schema físico en PostgreSQL
        await db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        await db.commit()

    print(f"✅  Schema '{schema}' creado en PostgreSQL")
    return schema


def run_tenant_migrations(schema: str) -> None:
    """Corre alembic upgrade head para el schema recién creado."""
    ini_content = f"""
[alembic]
script_location = {ROOT}/alembic/tenant
prepend_sys_path = {ROOT}
timezone = UTC
sqlalchemy.url = placeholder

[loggers]
keys = root,sqlalchemy,alembic
[handlers]
keys = console
[formatters]
keys = generic
[logger_root]
level = WARN
handlers = console
qualname =
[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine
[logger_alembic]
level = INFO
handlers =
qualname = alembic
[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic
[formatter_generic]
format = %%(levelname)-5.5s [%%(name)s] %%(message)s
datefmt = %%H:%%M:%%S
"""
    tmp_ini = ROOT / ".alembic_tenant_tmp.ini"
    tmp_ini.write_text(ini_content)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["TENANT_SCHEMA"] = schema

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(tmp_ini), "upgrade", "head"],
        env=env,
        cwd=str(ROOT),
    )
    tmp_ini.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"❌  Migraciones fallaron para schema '{schema}'")
        sys.exit(1)

    print(f"✅  Migraciones aplicadas en '{schema}'")


async def main(slug: str, name: str, email: str):
    print(f"\n🚀  Provisionando tenant '{name}' (slug: {slug})")
    schema = await provision_tenant(slug, name, email)
    run_tenant_migrations(schema)
    print(f"\n🎉  Tenant '{name}' listo.")
    print(f"     Siguiente: python scripts/seed_admin.py {slug} <email> <password>")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: create_tenant.py <slug> <name> <email>")
        sys.exit(1)
    asyncio.run(main(*sys.argv[1:]))
