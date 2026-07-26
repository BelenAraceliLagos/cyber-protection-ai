"""add_company_id_to_opportunities

Agrega la columna company_id (empresa emisora) a la tabla opportunities,
para poder segmentar el Kanban de oportunidades por marca/empresa emisora.

INSTRUCCIONES para generar el archivo real:
  1. alembic heads   (para confirmar tu head actual)
  2. alembic revision --head <TU_HEAD_ACTUAL> -m "add_company_id_to_opportunities"
  3. Reemplaza el cuerpo del archivo generado con el de abajo (deja su
     revision/down_revision tal como Alembic los generó)
  4. alembic upgrade <el_id_generado>
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
    if not _has_column("opportunities", "company_id"):
        op.add_column(
            "opportunities",
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True),
        )


def downgrade():
    if _has_column("opportunities", "company_id"):
        op.drop_column("opportunities", "company_id")
