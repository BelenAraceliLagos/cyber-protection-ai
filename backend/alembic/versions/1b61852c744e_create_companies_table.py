"""create companies table

Revision ID: 1b61852c744e
Revises: 5c2a6dc5fa0b
Create Date: 2026-06-18 15:31:52.683749
"""
from alembic import op
import sqlalchemy as sa


revision = '1b61852c744e'
down_revision = '5c2a6dc5fa0b'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "companies",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True
        ),

        sa.Column(
            "name",
            sa.String(),
            nullable=False
        ),

        sa.Column(
            "logo_path",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "background_path",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "primary_color",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "secondary_color",
            sa.String(),
            nullable=True
        ),

        sa.Column(
            "active",
            sa.Boolean(),
            server_default="true",
            nullable=False
        )
    )


def downgrade():

    op.drop_table("companies")
