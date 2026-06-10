.PHONY: up down build logs shell \
        migrate-public migrate-tenants migrate-tenant \
        migrate-public-down migrate-tenant-down \
        migration-status test create-tenant seed-admin

# ── Docker ────────────────────────────────────────────────────────────────────
up:
	cd infra && docker compose up -d

down:
	cd infra && docker compose down

build:
	cd infra && docker compose build --no-cache

logs:
	cd infra && docker compose logs -f api worker-notifications worker-inference

shell:
	cd infra && docker compose exec api bash

# ── Migraciones ───────────────────────────────────────────────────────────────

## Schema public (tabla tenants)
migrate-public:
	cd infra && docker compose exec api python scripts/migrate.py public upgrade head

migrate-public-down:
	cd infra && docker compose exec api python scripts/migrate.py public downgrade -1

## Todos los tenants
migrate-tenants:
	cd infra && docker compose exec api python scripts/migrate.py tenant upgrade head

## Tenant específico:  make migrate-tenant SLUG=acme
migrate-tenant:
	cd infra && docker compose exec api python scripts/migrate.py tenant upgrade head $(SLUG)

## Rollback tenant específico
migrate-tenant-down:
	cd infra && docker compose exec api python scripts/migrate.py tenant downgrade -1 $(SLUG)

## Estado actual de todas las migraciones
migration-status:
	@echo "=== PUBLIC ==="
	cd infra && docker compose exec api python scripts/migrate.py public current
	@echo "\n=== TENANTS ==="
	cd infra && docker compose exec api python scripts/migrate.py tenant current

# ── Setup inicial ─────────────────────────────────────────────────────────────

## make create-tenant SLUG=acme NAME="Acme Corp" EMAIL=admin@acme.com
create-tenant:
	cd infra && docker compose exec api python scripts/create_tenant.py $(SLUG) "$(NAME)" $(EMAIL)

## make seed-admin SLUG=acme EMAIL=admin@acme.com PASS=MiPass1
seed-admin:
	cd infra && docker compose exec api python scripts/seed_admin.py $(SLUG) $(EMAIL) $(PASS)

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest tests/ -v --asyncio-mode=auto

test-unit:
	pytest tests/unit/ -v --asyncio-mode=auto

test-integration:
	pytest tests/integration/ -v --asyncio-mode=auto
