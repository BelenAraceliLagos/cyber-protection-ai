"""add portada_path interior_path portada_config to companies

Revision ID: add_portada_interior_v1
Revises: c2e694a82d02
Create Date: 2026-06-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'add_portada_interior_v1'
down_revision = 'c2e694a82d02'
branch_labels = None
depends_on = None


def upgrade():
    # Agregar columnas que faltaban en la migración original de companies
    with op.batch_alter_table('companies') as batch_op:
        batch_op.add_column(
            sa.Column('portada_path', sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('interior_path', sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('portada_config', sa.JSON(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('companies') as batch_op:
        batch_op.drop_column('portada_config')
        batch_op.drop_column('interior_path')
        batch_op.drop_column('portada_path')
