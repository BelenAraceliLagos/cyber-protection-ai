"""add_updated_at_to_opportunities

Agrega opportunities.updated_at, necesario para calcular hace cuántos
días una oportunidad no tiene movimiento (alertas de estancamiento).

INSTRUCCIONES para generar el archivo real:
  1. alembic heads   (para confirmar tu head actual)
  2. alembic revision --head <TU_HEAD_ACTUAL> -m "add_updated_at_to_opportunities"
  3. Reemplaza el cuerpo del archivo generado con el de abajo (deja su
     revision/down_revision tal como Alembic los generó)
  4. alembic upgrade <el_id_generado>

Alternativa rápida sin Alembic (SQL directo en pgAdmin):

    ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "REEMPLAZAR_CON_EL_GENERADO"
down_revision = "REEMPLAZAR_CON_TU_HEAD_ACTUAL"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    if not _has_column("opportunities", "updated_at"):
        op.add_column(
            "opportunities",
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade():
    if _has_column("opportunities", "updated_at"):
        op.drop_column("opportunities", "updated_at")
