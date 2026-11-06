# Decisiones del proyecto

## D-05 · Propiedad de los datos (H-A02)
- **Fecha:** 2026-11-04
- **Contexto:** el sistema lo usa una sola persona (Andrés). El equipo de desarrollo mantiene una copia y no altera su versión hasta que la copia esté completamente operativa.
- **Decisión:** modelo de **equipo compartido**. Todo usuario con sesión iniciada puede ver, editar, borrar y exportar los clientes, oportunidades y cotizaciones. No se filtra por creador.
- **Protecciones vigentes:** acceso solo con sesión (H-A01), cuentas creadas solo por el administrador (H-A17) y catálogo de servicios solo para administrador (H-A14).
- **Cuándo revisar:** al incorporar más vendedores. Opciones a evaluar: (2) editar o borrar solo lo propio, salvo el administrador; (3) cada vendedor ve solo lo suyo.

## H-A21 · Roles
- **Fecha:** 2026-11-04
- **Decisión:** `users.role` ("admin" o "user") es la única fuente de autorización. Las tablas `Role` y `UserRole` quedan como **residuales**, sin uso, y están marcadas en el código.
- **Pendiente:** decidir con Andrés si se integran o se eliminan.

## D-06 · Código no activo: `ai.py` y webhooks (H-A04)
- **Fecha:** 2026-11-06
- **Hallazgo:** `routers/ai.py` y `api/webhooks.py` existen pero no están registrados en `main.py`.
- **Decisión:** quedan **sin registrar, a propósito**, y cada archivo lleva un encabezado que lo explica.
  - `ai.py` funciona, pero el frontend no lo usa: la IA de propuestas pasa por `proposal.py` y `generate_proposal.py`.
  - `webhooks.py` **no se activa** porque no valida clave: cualquiera podría crear clientes por internet.
- **Para activar el webhook:** exigir `WEBHOOK_API_KEY` desde el `.env` (401 si falta o no coincide), registrar el router y limitar la frecuencia de llamadas.
- **Pendiente con Andrés:** si el sitio web debe enviar prospectos al sistema.

## D-07 · Regla de capas para código nuevo (H-A05)
- **Fecha:** 2026-11-06
- **Hallazgo:** varios routers consultan la base de datos directamente, y otros usan `services/`.
- **Regla desde hoy (solo para código nuevo o que se toque):**
  1. El **router** solo recibe la petición, valida permisos y devuelve la respuesta.
  2. La **lógica de negocio y las consultas** viven en `app/services/`, en funciones que no dependen de FastAPI (así se pueden probar solas).
  3. Los **esquemas** (`schemas/`) validan los datos de entrada y salida.
- **Ejemplo ya aplicado:** el importador de catálogo (`services/catalogo_excel.py`, `services/catalogo_validacion.py`) es lógica pura probada sin base de datos; `routers/ingestion.py` solo conecta las piezas.
- **Lo existente no se reescribe de golpe:** se migra router por router cuando haya que modificarlo, para no arriesgar la versión que usa Andrés.

## D-08 · Funcionamiento sin internet (H-A07)
- **Fecha:** 2026-11-06
- **Estado:** el requisito de operar sin internet **no está confirmado**.
- **Dependencias externas del frontend hoy:** Google Fonts (tipografía DM Sans), Tabler Icons desde jsDelivr (`@latest`, sin versión fija) y Chart.js desde cdnjs (una página). SheetJS se retiró al reemplazar el importador. Ollama es local.
- **Opciones:** (A) copiar fuentes, íconos y Chart.js a `frontend/assets/vendor/` y fijar versiones: ~1 hora, funciona sin internet; (B) aceptar que se necesita internet para ver el diseño.
- **Pendiente con Andrés:** ¿el sistema debe funcionar sin internet? Hasta entonces, sin cambios.

## D-09 · Definición de Cliente y Empresa (H-A09)
- **Fecha:** 2026-11-06
- **Definición vigente en el código (AS-IS), que se adopta como oficial:**
  - **Client (cliente):** la organización a la que se le vende, con su contacto (`contact_name`, `email`, `phone`, `contact_position`), datos tributarios (`rut`, `business_name`) y etapa del ciclo de vida.
  - **Company (empresa emisora):** quien emite la cotización: marca (logo, colores, portada), RUT, dirección, banco y condiciones de pago. Hoy es Cyber-Protection.
  - **Emisor de una cotización:** `quotations.company_id`. **Contacto del cliente:** los campos de contacto de `Client`.
- **Pendiente:** confirmar con Andrés si hará falta más de un contacto por cliente (hoy hay uno solo).

## D-10 · Compliance (H-A10)
- **Fecha:** 2026-11-06
- **Estado:** **no existe** módulo de Compliance. No hay backend, tabla ni pantalla. El texto "Compliance" aparece solo como nombre de una categoría de servicios.
- **Decisión:** no declarar cumplimiento ni mostrar el módulo hasta resolver la decisión D-03 del informe (alcance del TO BE).

## D-11 · Opción "Sin IA" (H-A15)
- **Fecha:** 2026-11-06
- **Estado:** hoy la IA (Ollama) es el único flujo de generación. Si Ollama falla, el sistema cae a clasificación por palabras clave. **No hay un selector "Sin IA"** en la interfaz.
- **Pendiente con Andrés:** ¿se necesita un modo manual explícito (texto genérico, sin IA)? Si sí, se agrega un selector en la pantalla de propuesta.

## D-12 · Instalación reproducible y secretos (H-A22, H-A20)
- **Fecha:** 2026-11-06
- **Hecho:** `requirements.txt` con **versiones fijas**, tomadas del entorno que funciona. Se ensayó una instalación limpia en un entorno vacío y la aplicación arranca (`pip check` sin conflictos).
- **Hecho (Docker, H-A20):** `generate_proposal.py` usaba `localhost:11434` fijo; ahora usa la misma variable `OLLAMA_URL` que el resto del sistema. `config.py` ya no depende de rutas de Windows.
- **Hecho:** el archivo `dockerignore` debe llamarse `.dockerignore` (sin el punto, Docker no lo lee y copia `venv/` a la imagen).
- **Pendiente (seguridad):**
  1. `database.py` conserva una contraseña de base de datos como valor por defecto en el código, y `backend/.env` no define `DATABASE_URL`. Pasos: definir `DATABASE_URL` en el `.env`, **cambiar la contraseña de PostgreSQL**, y recién entonces quitar el valor por defecto del código.
  2. `INSTRUCCIONES.md` y otros documentos citaban una contraseña en texto plano. Se retiró del documento, pero **como pudo quedar en el historial de Git, hay que cambiarla.**
  3. `docker-compose.yml` tiene una contraseña de ejemplo para la base local de Docker.
