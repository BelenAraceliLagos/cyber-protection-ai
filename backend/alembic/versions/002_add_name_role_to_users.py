"""Agrega columnas de perfil a usuarios existentes.

Revision ID: 002_add_name_role_to_users
Revises: 001_initial_schema
Create Date: 2026-06-09
"""
from alembic import op

revision = "002_add_name_role_to_users"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR")
    op.execute(
        """
        UPDATE users
        SET name = split_part(email, '@', 1)
        WHERE name IS NULL OR btrim(name) = ''
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN name SET NOT NULL")

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR")
    op.execute(
        """
        UPDATE users
        SET role = 'user'
        WHERE role IS NULL OR btrim(role) = ''
        """
    )


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS name")
