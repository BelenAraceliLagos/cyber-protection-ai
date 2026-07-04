"""sync_missing_columns - agrega company_id a quotations si falta

Esta migración es idempotente: revisa si la columna ya existe antes de
agregarla, para que sea segura de correr tanto en bases que ya la tienen
(vía el ALTER TABLE manual que se aplicó como parche) como en bases que no.

INSTRUCCIONES:
1. Corre `alembic heads` y `alembic current` para confirmar tu revisión actual.
2. Genera el archivo real con:
     alembic revision -m "sync_missing_columns"
   Esto crea un archivo con `revision` y `down_revision` ya correctos
   (apuntando a tu head actual).
3. Reemplaza el contenido de `upgrade()` y `downgrade()` de ese archivo
   generado con el de este archivo (deja su `revision`/`down_revision`
   tal como Alembic los generó, no los de aquí).
4. Corre `alembic upgrade head`.
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
    if not _has_column("quotations", "company_id"):
        op.add_column(
            "quotations",
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True),
        )


def downgrade():
    if _has_column("quotations", "company_id"):
        op.drop_column("quotations", "company_id")
