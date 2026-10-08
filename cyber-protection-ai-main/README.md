# Cyber Protection AI

Sistema inteligente para generación automática de informes
y cotizaciones de servicios de ciberseguridad utilizando IA local.

## Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- Ollama
- JWT

## Migraciones de base de datos

El proyecto **ya no usa Alembic**. En su lugar, usa un sistema simple de
archivos `.sql` numerados (carpeta `backend/migrations/`), aplicados por
`backend/apply_migrations.py`.

Para poner la base de datos al día (funciona tanto en una instalación
nueva como en una que ya tiene datos):

```bash
cd backend
venv\Scripts\python.exe apply_migrations.py   # Windows
# o: python apply_migrations.py                # Linux/Mac
```

Este comando hace dos cosas, en orden, y es seguro de correr todas las
veces que quieras:

1. Crea cualquier tabla que falte, según los modelos actuales de
   `app/models/` (`Base.metadata.create_all()`).
2. Aplica, en orden, los archivos `.sql` de `backend/migrations/` que
   todavía no se hayan aplicado — llevando el registro en una tabla
   `schema_migrations`.

Cada cambio futuro en tablas o columnas debe agregarse como un archivo
`.sql` nuevo en `backend/migrations/`, numerado en orden (`0004_...sql`,
`0005_...sql`, etc.), escrito de forma idempotente (`IF NOT EXISTS`).
Ver `backend/migrations/README.md` para el detalle completo.

