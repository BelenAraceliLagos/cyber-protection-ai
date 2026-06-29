"""merge head

Revision ID: c2e694a82d02
Revises: 003_client_company_profile, 1b61852c744e
Create Date: 2026-06-18 16:34:32.512214
"""
from alembic import op
import sqlalchemy as sa


revision = 'c2e694a82d02'
down_revision = ('003_client_company_profile', '1b61852c744e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
