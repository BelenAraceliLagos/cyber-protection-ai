"""Agrega campos de empresa y contacto a clientes.

Revision ID: 003_client_company_profile
Revises: 002_add_name_role_to_users
Create Date: 2026-06-11
"""
from alembic import op

revision = "003_client_company_profile"
down_revision = "002_add_name_role_to_users"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS rut VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS business_name VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS address VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS city VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS region VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS country VARCHAR DEFAULT 'Chile'")
    op.execute("UPDATE clients SET country = 'Chile' WHERE country IS NULL OR btrim(country) = ''")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS website VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS contact_position VARCHAR")
    op.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS contact_phone VARCHAR")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_clients_rut ON clients (rut) WHERE rut IS NOT NULL")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_clients_rut")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS contact_phone")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS contact_position")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS website")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS country")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS region")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS city")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS address")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS business_name")
    op.execute("ALTER TABLE clients DROP COLUMN IF EXISTS rut")
