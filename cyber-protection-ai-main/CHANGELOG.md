# Registro de cambios

Formato: fecha · qué cambió. Cada cambio de esquema tiene su migración numerada en `backend/migrations/`.

## Línea base — 2026-11-06
Punto de partida documentado para el trabajo sobre el informe AS-IS v2.4. A partir de aquí, todo cambio relevante se anota en este archivo.

### Hallazgos del informe resueltos hasta la línea base
Seguridad de acceso (H-A01, H-A14, H-A17), validaciones de precio, cantidad y correo, errores legibles en pantalla, ciclo de venta real en el CRM, cierre de oportunidades, roles (decisión documentada), modelo de datos compartido (D-05), importancia de hitos y edición/borrado de hitos en el Gantt.

### Nuevo
- **Modalidad de servicio** como columna propia (`0006`), editable en la pantalla de Servicios y visible como etiqueta.
- **Importador de catálogo desde Excel** con vista previa obligatoria, validaciones fila por fila y confirmación (`/ingestion/catalogo/preview` y `/confirmar`).
- Plantilla `Plantilla_Catalogo_Servicios.xlsx` (53 servicios) y comparación con el brochure 2026.
- 5 servicios nuevos desde el brochure; 5 servicios existentes actualizados (CIS v8.1, vCISO, Ley 21.719, IR, NERC CIP).

### Cambiado
- `requirements.txt` con versiones fijas.
- `config.py` portable (Windows/Linux/Docker); `generate_proposal.py` usa `OLLAMA_URL`.
- Eliminado código sin uso: `generatePDF` (oportunidades), `reportAPI` e `importAPI` (api.js), SheetJS.
- `ai.py` y `webhooks.py` documentados como no activos (D-06).
- El enlace "Historial" del menú se oculta hasta que el módulo esté listo.
