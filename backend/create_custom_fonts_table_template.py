"""create_custom_fonts_table

Crea la tabla custom_fonts, para guardar las fuentes personalizadas
subidas desde "Gestión de Datos" y usadas en el Editor de diseño / PDF.

Idempotente: revisa si la tabla ya existe antes de crearla.

INSTRUCCIONES para generar el archivo real:
  1. alembic revision --head <TU_HEAD_ACTUAL> -m "create_custom_fonts_table"
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
