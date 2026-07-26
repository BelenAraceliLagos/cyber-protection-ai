"""
apply_migrations.py — Crea el esquema completo desde los modelos de SQLAlchemy
y aplica encima las migraciones SQL sueltas de la carpeta migrations/.

Uso (dentro del contenedor o con el venv activo):
    python apply_migrations.py

Es seguro correrlo varias veces: create_all() no toca tablas que ya existen,
y cada migración SQL solo se aplica una vez (se registra en schema_migrations).
"""

from pathlib import Path
from sqlalchemy import text

from app.core.database import Base, engine

# Importar TODOS los modelos para que SQLAlchemy los registre en Base.metadata
# antes de llamar a create_all(). No hace falta usar las clases, solo que el
# import se ejecute.
import app.models.client
import app.models.user
import app.models.service
import app.models.quotation
import app.models.quotation_item
import app.models.opportunity
import app.models.milestone
import app.models.company
import app.models.custom_font
import app.models.profile
import app.models.role
import app.models.user_role
import app.models.activity_note

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def crear_tabla_control(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename    TEXT PRIMARY KEY,
            applied_at  TIMESTAMP NOT NULL DEFAULT now()
        )
    """))


def migraciones_aplicadas(conn):
    rows = conn.execute(text("SELECT filename FROM schema_migrations")).fetchall()
    return {r[0] for r in rows}


def aplicar_migraciones_sql(conn):
    if not MIGRATIONS_DIR.exists():
        print(f"  (sin carpeta migrations/ en {MIGRATIONS_DIR}, se omite)")
        return

    aplicadas = migraciones_aplicadas(conn)
    archivos = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not archivos:
        print("  No hay archivos .sql en migrations/")
        return

    for archivo in archivos:
        if archivo.name in aplicadas:
            print(f"  ⏭️  {archivo.name} (ya aplicada, se omite)")
            continue

        print(f"  ▶️  Aplicando {archivo.name} ...")
        sql = archivo.read_text(encoding="utf-8")
        conn.execute(text(sql))
        conn.execute(
            text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
            {"f": archivo.name}
        )
        print(f"  ✅ {archivo.name} aplicada")


def main():
    print("🔧 Creando esquema base desde los modelos de SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("✅ Esquema base creado (o ya existía).\n")

    print("🔧 Revisando migraciones SQL pendientes en migrations/ ...")
    with engine.begin() as conn:
        crear_tabla_control(conn)
        aplicar_migraciones_sql(conn)

    print("\n🚀 Listo. Base de datos al día.")


if __name__ == "__main__":
    main()
