"""
Orquestador de migraciones multi-tenant.

Uso:
    python scripts/migrate.py public upgrade head       # migra schema public
    python scripts/migrate.py tenant upgrade head       # migra TODOS los tenants
    python scripts/migrate.py tenant upgrade head acme  # migra solo tenant 'acme'
    python scripts/migrate.py tenant current            # estado actual de todos
    python scripts/migrate.py tenant downgrade -1 acme  # rollback tenant 'acme'
"""
import asyncio
import os
import subprocess
import sys
from pathlib import Path

# Agrega el root al path para importar app.*
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def get_all_tenant_schemas() -> list[str]:
    """Lee todos los schema_name de la tabla public.tenants."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT schema_name FROM tenants WHERE is_active = true ORDER BY created_at")
        )
        return [row[0] for row in result.fetchall()]


def run_alembic(env: str, args: list[str], schema: str | None = None) -> int:
    """Llama a alembic con el entorno correcto."""
    env_vars = os.environ.copy()
    env_vars["PYTHONPATH"] = str(ROOT)

    if schema:
        env_vars["TENANT_SCHEMA"] = schema

    cmd = [
        sys.executable, "-m", "alembic",
        "-c", str(ROOT / "alembic.ini"),
        "--config", str(ROOT / f"alembic/{env}/env.py"),  # no es un flag real, lo leemos abajo
    ]

    # Alembic no acepta --config para env.py, usamos la variable de entorno
    # y apuntamos script_location al dir correcto
    cmd = [
        sys.executable, "-m", "alembic",
        "-c", str(ROOT / "alembic.ini"),
        *args,
    ]

    # Sobreescribir script_location inline via -x no funciona bien;
    # usamos directamente el ini que apunta al env correcto
    ini_content = f"""
[alembic]
script_location = {ROOT}/alembic/{env}
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
    tmp_ini = ROOT / f".alembic_{env}.ini"
    tmp_ini.write_text(ini_content)

    cmd = [sys.executable, "-m", "alembic", "-c", str(tmp_ini), *args]
    result = subprocess.run(cmd, env=env_vars, cwd=str(ROOT))
    tmp_ini.unlink(missing_ok=True)
    return result.returncode


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]        # public | tenant
    alembic_args = sys.argv[2:] # upgrade head | downgrade -1 | current | ...

    # Extrae slug opcional al final (solo para tenant)
    slug_filter = None
    if target == "tenant" and len(alembic_args) > 0:
        last = alembic_args[-1]
        if last not in ("head", "base", "current", "history") and not last.startswith("-"):
            # Puede ser un slug o un revision id; heurística: sin números largos = slug
            if len(last) < 20:
                slug_filter = last
                alembic_args = alembic_args[:-1]

    if target == "public":
        print("▶  Migrando schema public...")
        code = run_alembic("public", alembic_args)
        sys.exit(code)

    elif target == "tenant":
        if slug_filter:
            schemas = [f"tenant_{slug_filter}"]
            print(f"▶  Migrando tenant: {schemas[0]}")
        else:
            schemas = await get_all_tenant_schemas()
            print(f"▶  Migrando {len(schemas)} tenant(s): {schemas}")

        failed = []
        for schema in schemas:
            print(f"\n── {schema} {'─' * (40 - len(schema))}")
            code = run_alembic("tenant", alembic_args, schema=schema)
            if code != 0:
                failed.append(schema)

        if failed:
            print(f"\n❌  Fallaron: {failed}")
            sys.exit(1)
        else:
            print(f"\n✅  Migraciones completadas ({len(schemas)} schemas)")
    else:
        print(f"Target desconocido: '{target}'. Usa 'public' o 'tenant'.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
