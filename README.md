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
No se debe modificar el esquema desde `start.sh` ni depender de `create_all` al iniciar el backend.

Para aplicar migraciones:

```bash
cd backend
alembic upgrade head
```

Si ya tienes una base local creada antes de Alembic, primero marca el baseline y luego aplica los cambios pendientes:

```bash
cd backend
alembic stamp 001_initial_schema
alembic upgrade head
```

Si vas a crear una base nueva desde cero, usa solo:

```bash
cd backend
alembic upgrade head
```

Cada cambio futuro en tablas o columnas debe agregarse como una nueva migracion de Alembic.
