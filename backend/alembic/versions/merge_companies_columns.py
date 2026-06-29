"""merge heads after adding portada interior columns

Revision ID: merge_companies_cols
Revises: add_portada_interior_v1, 95dd704e9592
Create Date: 2026-06-27 00:01:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'merge_companies_cols'
down_revision = ('add_portada_interior_v1', '95dd704e9592')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
