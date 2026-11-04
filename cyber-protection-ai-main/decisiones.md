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