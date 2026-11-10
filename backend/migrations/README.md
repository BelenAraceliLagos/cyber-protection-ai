# Migraciones — sistema simple (sin Alembic)

Este proyecto ya no usa Alembic. En su lugar, usa archivos `.sql` numerados
en esta carpeta, aplicados por `backend/apply_migrations.py`.

## Cómo aplicar las migraciones pendientes

```powershell
cd backend
venv\Scripts\python.exe apply_migrations.py
```

Esto hace dos cosas, en orden:
1. Crea cualquier tabla que falte, según los modelos actuales de
   `app/models/` (útil en una instalación nueva, en un equipo que nunca
   tuvo la base de datos).
2. Aplica, en orden, los archivos `.sql` de esta carpeta que todavía no
   se hayan aplicado — llevando el registro en una tabla
   `schema_migrations` (una fila por archivo ya aplicado).

Es seguro correr este comando **todas las veces que quieras** — si no hay
nada pendiente, no hace nada.

## Cómo agregar una migración nueva

Cuando necesites un cambio de esquema (una columna nueva, una tabla
nueva, etc.):

1. Crea un archivo nuevo en esta carpeta, con el **próximo número**
   disponible y un nombre descriptivo:
   ```
   0004_agrega_algo_nuevo.sql
   ```
2. Escribe el SQL — **siempre de forma idempotente** (que no falle si se
   corre dos veces), usando `IF NOT EXISTS` / `IF EXISTS`:
   ```sql
   ALTER TABLE clients ADD COLUMN IF NOT EXISTS ejemplo VARCHAR;
   ```
3. Corre `apply_migrations.py` para aplicarla.
4. Sube el archivo `.sql` al repositorio (o compártelo con tu compañero)
   junto con el resto de tus cambios de código — así, cuando la otra
   persona corra `apply_migrations.py` en su equipo, se aplica sola.

## Reglas simples

- **Nunca edites un archivo `.sql` que ya fue aplicado** (ni por ti ni por
  tu compañero) — si necesitas cambiar algo, crea un archivo nuevo con el
  siguiente número.
- **Nunca borres un archivo `.sql`** de esta carpeta una vez compartido —
  otros equipos podrían no haberlo aplicado todavía.
- El orden de aplicación es el **orden alfabético de los nombres** — por
  eso el número al principio (`0001_`, `0002_`...) importa.

## Migraciones actuales

| Archivo | Qué hace |
|---|---|
| `0001_add_updated_at_opportunities.sql` | Agrega `opportunities.updated_at` (alertas de estancamiento) |
| `0002_add_lifecycle_auto_clients.sql` | Agrega `clients.lifecycle_auto` (etapa automática vs. congelada) |
| `0003_add_plazo_meses_opportunities.sql` | Agrega `opportunities.plazo_meses` (3/6/9/12 meses) |
