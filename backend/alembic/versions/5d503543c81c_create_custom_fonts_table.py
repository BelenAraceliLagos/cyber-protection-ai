"""create_custom_fonts_table

Revision ID: 5d503543c81c
Revises: 23dced809af2
Create Date: 2026-07-06 17:34:09.155358
"""
from alembic import op
import sqlalchemy as sa


revision = '5d503543c81c'
down_revision = '23dced809af2'
branch_labels = None
depends_on = None

def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not _has_table("custom_fonts"):
        op.create_table(
            "custom_fonts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("css_key", sa.String(), nullable=False, unique=True),
            sa.Column("regular_path", sa.String(), nullable=True),
            sa.Column("bold_path", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    if _has_table("custom_fonts"):
        op.drop_table("custom_fonts")
