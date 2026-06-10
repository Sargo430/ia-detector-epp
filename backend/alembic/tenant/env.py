"""
Alembic env para schemas TENANT.
Se ejecuta una vez por schema (tenant_*).
El schema objetivo se pasa via variable de entorno TENANT_SCHEMA.
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import settings
from app.db.base import Base

# Importa TODOS los modelos que viven en tenant schemas
from app.models.user import User
from app.models.camera import Camera
from app.models.event import Event
from app.models.alert import Alert

TENANT_SCHEMA = os.environ.get("TENANT_SCHEMA", "")
if not TENANT_SCHEMA:
    raise RuntimeError("TENANT_SCHEMA env var is required for tenant migrations")

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("+asyncpg", "")
)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Solo incluye tablas sin schema explícito (se mapearán al search_path activo)."""
    if type_ == "table":
        schema = getattr(object, "schema", None)
        if schema and schema != TENANT_SCHEMA:
            return False
    return True


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_object,
        version_table="alembic_version",
        version_table_schema=TENANT_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Todas las DDL van al schema del tenant
        connection.execute(text(f"SET search_path TO {TENANT_SCHEMA}, public"))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            version_table="alembic_version",
            version_table_schema=TENANT_SCHEMA,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
