"""Esquema base actual de Cyber Protection AI.

Revision ID: 001_esquema_base_actual
Revises:
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "001_esquema_base_actual"
down_revision = None
branch_labels = None
depends_on = None


etapa_venta = postgresql.ENUM(
    "prospecto",
    "propuesta",
    "negociacion",
    "aprobacion",
    "ganado",
    "perdido",
    name="etapaventa",
    create_type=False,
)

tipo_hito = postgresql.ENUM(
    "reunion",
    "entrega_propuesta",
    "seguimiento",
    "negociacion",
    "firma",
    "inicio_servicio",
    "otro",
    name="tipohito",
    create_type=False,
)


def upgrade():
    bind = op.get_bind()
    etapa_venta.create(bind, checkfirst=True)
    tipo_hito.create(bind, checkfirst=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=False),
        sa.Column("contact_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("rut", sa.String(), nullable=True),
        sa.Column("business_name", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("country", sa.String(), server_default="Chile", nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("contact_position", sa.String(), nullable=True),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(
        "ix_clients_rut",
        "clients",
        ["rut"],
        unique=True,
        postgresql_where=sa.text("rut IS NOT NULL"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_roles_id"), "roles", ["id"], unique=False)

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_price", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_services_id"), "services", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), server_default="user", nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("etapa", etapa_venta, nullable=False),
        sa.Column("probabilidad", sa.Integer(), nullable=True),
        sa.Column("valor_uf", sa.Float(), nullable=True),
        sa.Column("industria", sa.String(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(), nullable=True),
        sa.Column("service_ids_str", sa.String(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_opportunities_id"), "opportunities", ["id"], unique=False)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("position", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_profiles_id"), "profiles", ["id"], unique=False)

    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("subtotal", sa.Float(), nullable=True),
        sa.Column("tax", sa.Float(), nullable=True),
        sa.Column("total", sa.Float(), nullable=True),
        sa.Column("generated_text", sa.Text(), nullable=True),
        sa.Column("pdf_path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotations_id"), "quotations", ["id"], unique=False)

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "activity_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("autor", sa.String(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activity_notes_id"), "activity_notes", ["id"], unique=False)

    op.create_table(
        "milestones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("tipo", tipo_hito, nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completado", sa.Boolean(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_milestones_id"), "milestones", ["id"], unique=False)

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=True),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quotation_items_id"), "quotation_items", ["id"], unique=False)


def downgrade():
    bind = op.get_bind()

    op.drop_table("quotation_items")
    op.drop_table("milestones")
    op.drop_table("activity_notes")
    op.drop_table("user_roles")
    op.drop_table("quotations")
    op.drop_table("profiles")
    op.drop_table("opportunities")
    op.drop_table("users")
    op.drop_table("services")
    op.drop_table("roles")
    op.drop_table("clients")

    tipo_hito.drop(bind, checkfirst=True)
    etapa_venta.drop(bind, checkfirst=True)
