-- Runs once when the container is created.
-- Creates the public tenants table.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- fast text search

CREATE TABLE IF NOT EXISTS tenants (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(120) NOT NULL,
    slug                VARCHAR(60)  NOT NULL UNIQUE,
    schema_name         VARCHAR(80)  NOT NULL UNIQUE,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    plan                VARCHAR(30)  NOT NULL DEFAULT 'starter',
    max_cameras         INTEGER      NOT NULL DEFAULT 5,
    max_retention_days  INTEGER      NOT NULL DEFAULT 30,
    contact_email       VARCHAR(254) NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants (slug);
