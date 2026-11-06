# Cyber Protection AI

Sistema para generar propuestas y cotizaciones de servicios de ciberseguridad,
con gestión de clientes, oportunidades (Kanban y Gantt), CRM y redacción asistida
por IA local (Ollama).

## Qué incluye
| Módulo | Qué hace |
|---|---|
| Clientes | Maestra de clientes y ciclo de vida |
| Servicios | Catálogo con precio base (UF) y modalidad; importación desde Excel con vista previa |
| Oportunidades | Pipeline Kanban, hitos y Gantt |
| CRM | Indicadores de ventas, ciclo de venta real |
| Generar informe | Propuesta en PDF con redacción asistida por IA |
| Empresas | Empresa emisora: marca, datos y condiciones |
| Gestión de Datos | Importar catálogo (Excel) y sincronizar módulos entre entornos (JSON) |

## Stack
FastAPI · SQLAlchemy · PostgreSQL · JWT · WeasyPrint · Ollama (`gemma3:4b`) · frontend en JavaScript sin framework.

## Cómo arrancar (Windows)
1. Ejecutar `start_pcp.bat` (carpeta superior). Levanta la base de datos, aplica las migraciones, y arranca backend (puerto 8080) y frontend (puerto 5500).
2. Abrir `http://localhost:5500/pages/login.html`.
3. Documentación interactiva de la API: `http://localhost:8080/docs`.

Si arrancas el backend a mano en Windows, define antes `WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin`; sin eso falla el PDF.

## Instalación desde cero
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Las versiones están fijas en `requirements.txt` (probadas en una instalación limpia). Configurar `backend/.env` con `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES`. Instrucciones completas: `MANUAL_INSTALACION.md`.

## Migraciones de base de datos
No se usa Alembic. Los cambios de esquema son archivos `.sql` numerados en `backend/migrations/`, escritos de forma idempotente y aplicados por `backend/apply_migrations.py` (lo ejecuta `start_pcp.bat`). Detalle: `backend/migrations/README.md`.

## Documentos de referencia
- `decisiones.md`: decisiones del proyecto y pendientes con el equipo.
- `CHANGELOG.md`: registro de cambios (línea base 2026-11-06).
- `INSTRUCCIONES.md` y `MANUAL.md`: **históricos (v2.0)**; no reflejan el estado actual.
