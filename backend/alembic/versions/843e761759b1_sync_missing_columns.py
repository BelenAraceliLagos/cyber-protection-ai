"""sync_missing_columns

Revision ID: 843e761759b1
Revises: add_content_color_v1
Create Date: 2026-07-03 17:29:10.679205
"""
from alembic import op
import sqlalchemy as sa


revision = '843e761759b1'
down_revision = 'add_content_color_v1'
branch_labels = None
depends_on = None

def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    if not _has_column("quotations", "company_id"):
        op.add_column(
            "quotations",
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True),
        )


def downgrade():
    if _has_column("quotations", "company_id"):
        op.drop_column("quotations", "company_id")