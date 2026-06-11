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

El proyecto usa Alembic para versionar cambios de estructura en PostgreSQL.
No se debe modificar el esquema desde `start.sh` ni depender de `create_all`
al iniciar el backend.

Si vas a crear una base nueva desde cero:

```bash
cd backend
../.venv/bin/python -m alembic upgrade head
```

Si restauraste el dump compartido por el equipo, la base ya trae la estructura
y los datos. En ese caso solo marca la base como alineada con la version actual:

```bash
cd backend
../.venv/bin/python -m alembic stamp head --purge
```

Para ver la version aplicada:

```bash
cd backend
../.venv/bin/python -m alembic current
```

Cada cambio futuro en tablas, columnas, enums o relaciones debe agregarse como
una nueva migracion de Alembic. Los archivos `.dump` y `.sql` no deben subirse
al repositorio.
