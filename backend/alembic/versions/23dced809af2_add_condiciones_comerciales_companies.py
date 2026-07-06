"""add_condiciones_comerciales_companies

Revision ID: 23dced809af2
Revises: 843e761759b1
Create Date: 2026-07-05 02:26:24.428512
"""
from alembic import op
import sqlalchemy as sa


revision = '23dced809af2'
down_revision = '843e761759b1'
branch_labels = None
depends_on = None


NUEVAS_COLUMNAS = [
    ("rut", sa.String()),
    ("direccion", sa.String()),
    ("telefono", sa.String()),
    ("notas_valores", sa.String()),
    ("formas_pago", sa.String()),
    ("modalidad_proyecto", sa.String()),
    ("modalidad_consultoria", sa.String()),
    ("banco", sa.String()),
    ("datos_bancarios", sa.String()),
]


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    for nombre, tipo in NUEVAS_COLUMNAS:
        if not _has_column("companies", nombre):
            op.add_column("companies", sa.Column(nombre, tipo, nullable=True))


def downgrade():
    for nombre, _ in NUEVAS_COLUMNAS:
        if _has_column("companies", nombre):
            op.drop_column("companies", nombre)