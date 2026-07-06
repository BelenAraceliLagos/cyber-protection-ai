"""add_condiciones_comerciales_companies

Agrega los campos de "Condiciones Comerciales" a la tabla companies, para
que cada empresa emisora tenga sus propios datos de RUT, dirección,
teléfono, formas de pago y datos bancarios — usados en la última página
de los informes generados (antes texto fijo, ahora por empresa).

Idempotente: revisa columna por columna antes de agregarla, para no
fallar si el entorno ya la tiene (ej. si se aplicó a mano antes).

INSTRUCCIONES para generar el archivo real:
  1. alembic revision --head <TU_HEAD_ACTUAL> -m "add_condiciones_comerciales_companies"
  2. Reemplaza el cuerpo del archivo generado con el de abajo (deja su
     `revision`/`down_revision` tal como Alembic los generó).
  3. alembic upgrade <el_id_generado>
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "REEMPLAZAR_CON_EL_GENERADO"
down_revision = "REEMPLAZAR_CON_TU_HEAD_ACTUAL"
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
