"""add_crm_fields

Agrega los campos necesarios para el módulo CRM:
- clients.lifecycle_stage, clients.origen, clients.created_at
- opportunities.created_at

INSTRUCCIONES para generar el archivo real:
  1. alembic heads   (para confirmar tu head actual)
  2. alembic revision --head <TU_HEAD_ACTUAL> -m "add_crm_fields"
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
    if not _has_column("clients", "lifecycle_stage"):
        op.add_column("clients", sa.Column("lifecycle_stage", sa.String(), nullable=True, server_default="lead"))
    if not _has_column("clients", "origen"):
        op.add_column("clients", sa.Column("origen", sa.String(), nullable=True))
    if not _has_column("clients", "created_at"):
        op.add_column("clients", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    if not _has_column("opportunities", "created_at"):
        op.add_column("opportunities", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))


def downgrade():
    if _has_column("opportunities", "created_at"):
        op.drop_column("opportunities", "created_at")
    if _has_column("clients", "created_at"):
        op.drop_column("clients", "created_at")
    if _has_column("clients", "origen"):
        op.drop_column("clients", "origen")
    if _has_column("clients", "lifecycle_stage"):
        op.drop_column("clients", "lifecycle_stage")
