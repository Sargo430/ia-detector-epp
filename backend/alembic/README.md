# Migraciones Multi-Tenant

## Arquitectura

```
alembic/
├── public/          ← schema "public" (tabla tenants)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_create_tenants.py
│       └── 0002_tenants_add_notifications_config.py
└── tenant/          ← cada schema tenant_* (users, cameras, events, alerts)
    ├── env.py
    ├── script.py.mako
    └── versions/
        ├── 0001_create_tenant_tables.py
        └── 0002_cameras_add_last_seen.py
```

Cada tenant tiene su propia tabla `alembic_version` dentro de su schema,
lo que permite aplicar migraciones independientemente por tenant.

## Comandos

```bash
# Setup inicial (primera vez)
make migrate-public          # crea tabla tenants en public
make create-tenant SLUG=acme NAME="Acme Corp" EMAIL=admin@acme.com
#  └── crea schema + corre migraciones de tenant automáticamente

# Ver estado
make migration-status

# Migrar todos los tenants (nueva migración desplegada)
make migrate-tenants

# Migrar un tenant específico
make migrate-tenant SLUG=acme

# Rollback
make migrate-public-down
make migrate-tenant-down SLUG=acme
```

## Crear una nueva migración

### Para el schema public (cambios en tabla tenants):
```bash
# Crear archivo manualmente en alembic/public/versions/
# Nombrar: NNNN_descripcion_corta.py
# down_revision debe apuntar al revision anterior
```

### Para todos los tenants (cambios en users/cameras/events/alerts):
```bash
# Crear archivo manualmente en alembic/tenant/versions/
# Se aplicará a TODOS los schemas tenant_* al correr migrate-tenants
```

## Reglas

1. Nunca edites una migración ya aplicada en producción.
2. Siempre implementa `downgrade()` para poder hacer rollback.
3. Las migraciones de tenant son idempotentes por diseño (IF NOT EXISTS).
4. Al agregar un nuevo tenant, `create_tenant.py` corre automáticamente
   todas las migraciones hasta `head` — no necesitas hacerlo manualmente.
