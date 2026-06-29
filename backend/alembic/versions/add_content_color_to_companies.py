"""add content_color to companies

Revision ID: add_content_color_v1
Revises: merge_companies_cols
Create Date: 2026-06-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_content_color_v1'
down_revision = 'merge_companies_cols'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('companies') as batch_op:
        batch_op.add_column(sa.Column('content_color', sa.String(), nullable=True))

def downgrade():
    with op.batch_alter_table('companies') as batch_op:
        batch_op.drop_column('content_color')
