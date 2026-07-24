# Cyber-Protection — Frontend

Sistema de preventas con IA local. Frontend en HTML + CSS (BEM, mobile first) + JavaScript vanilla.

## Estructura

```
cyber-protection-frontend/
├── index.html              → redirige al login
├── pages/
│   ├── login.html          → autenticación
│   ├── dashboard.html      → bienvenida + módulos
│   ├── clients.html        → CRUD clientes (completo)
│   ├── services.html       → catálogo servicios (stub)
│   ├── usuarios.html       → gestión de usuarios admin
│   ├── report.html         → generador Ollama (completo)
│   └── import.html         → importación históricos (stub)
├── css/
│   ├── base.css            → variables, reset, tipografía
│   ├── animations.css      → todas las animaciones
│   ├── layout.css          → sidebar, topbar, grid (mobile first)
│   ├── components.css      → btn, card, badge, alert, table, modal...
│   └── pages/              → estilos específicos por página
├── js/
│   ├── api.js              → ÚNICO lugar con fetch() — todos los endpoints
│   ├── auth.js             → login, logout, token JWT
│   ├── sidebar.js          → colapsar/expandir, menú mobile
│   ├── clients.js          → lógica completa del módulo clientes
│   ├── report.js           → generación con Ollama + spinner
│   └── utils.js            → alertas, skeleton, modales, fechas, etc.
└── assets/                 → logo, favicon
```

## Cómo correr

Necesitas un servidor local (los módulos ES no funcionan abriendo el HTML directamente).

```bash
# Opción 1: Python
cd cyber-protection-frontend
python3 -m http.server 3000

# Opción 2: Node
npx serve .
```

Abre http://localhost:3000

## Conexión con el backend

Edita `js/api.js` y cambia `BASE_URL`:

```js
const BASE_URL = 'http://localhost:8080'  // URL del backend FastAPI
```

## Endpoints que consume

| Módulo     | Endpoint                        | Estado backend |
|------------|---------------------------------|----------------|
| Login      | POST /auth/login                | ✅ Listo       |
| Clientes   | GET/POST/PUT/DELETE /clients    | ✅ Listo       |
| Servicios  | GET/POST/PUT/DELETE /services   | ⚠️ Falta router|
| Informe IA | POST /reports/generate          | ❌ Pendiente   |
| Importar   | POST /import/quotes             | ❌ Pendiente   |

## Notas

- El token JWT se guarda en `sessionStorage` (se limpia al cerrar el navegador)
- Todos los fetch() pasan por `api.js` — nunca directamente en los módulos
- Las animaciones respetan `prefers-reduced-motion`
- Los módulos sin backend muestran un empty state hasta que los endpoints estén listos
