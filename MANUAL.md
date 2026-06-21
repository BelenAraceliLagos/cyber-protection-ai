# Cyber-Protection AI — Manual de Instalación v2.0

---

## Requisitos previos

| Componente | Versión mínima |
|---|---|
| Python | 3.10+ |
| PostgreSQL | 14+ |
| Node.js | No requerido |
| RAM | 8 GB (16 GB recomendado para Ollama) |
| GPU | Opcional — acelera IA significativamente |

---

## PARTE 1 — Instalación del Backend

### 1.1 Descomprimir el proyecto

Descomprime el ZIP en tu carpeta de trabajo. La estructura debe quedar así:

```
cyber-protection-ai-main/
├── app/
├── assets/          ← copiar imágenes aquí
├── frontend/
├── propuestas_generadas/
├── uploads_tmp/
├── .env
├── requirements.txt
└── MANUAL.md
```

### 1.2 Crear entorno virtual

```powershell
cd cyber-protection-ai-main
python -m venv venv --clear
.\venv\Scripts\Activate.ps1
```

### 1.3 Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 1.4 Configurar PostgreSQL

1. Descarga e instala PostgreSQL desde https://www.postgresql.org/download/windows/
2. Durante la instalación anota la contraseña del usuario `postgres`
3. Abre **pgAdmin** y crea la base de datos:
   - Clic derecho en **Databases → Create → Database**
   - Nombre: `cyber_protection_ai`

4. Si tu contraseña de PostgreSQL es diferente a `linkinpark1`, edita el archivo `.env`:

```
DATABASE_URL=postgresql://postgres:TU_CONTRASEÑA@localhost:5432/cyber_protection_ai
SECRET_KEY=super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### 1.5 Arrancar el servidor

```powershell
uvicorn app.main:app --reload --port 8000
```

Deberías ver:
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

### 1.6 Crear el primer usuario administrador

Con el servidor corriendo, genera un hash de contraseña:

```powershell
python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print(ctx.hash('admin123'))"
```

Copia el hash generado (empieza con `$2b$12$...`) y ejecuta en pgAdmin:

```sql
-- Paso 1: Insertar usuario
INSERT INTO users (name, email, hashed_password, role)
VALUES ('admin@cyberprotection.cl', '$2b$12$y6CdCGiFCUDZh3RSRubgE.i9cRehruUa02h599Hzwmt8ZspCcmjUG', true);

-- Paso 2: Ver el id asignado
SELECT id FROM users WHERE email = 'admin@cyberprotection.cl';

-- Paso 3: Insertar perfil (reemplaza X con el id del paso 2)
INSERT INTO profiles (user_id, name) VALUES (X, 'Administrador');

-- Paso 4: Ver el id del rol admin
SELECT id FROM roles WHERE name = 'admin';

-- Paso 5: Asignar rol (reemplaza X e Y con los ids correspondientes)
INSERT INTO user_roles (user_id, role_id) VALUES (X, Y);
```

**Credenciales de acceso:**
- Email: `admin@cyberprotection.cl`
- Contraseña: `admin123`

### 1.7 Copiar assets de imagen

Copia los archivos de imagen a la carpeta `assets/`:

```
logo_cyberprotection.jpg   → assets/logo_cyberprotection.jpg
foto_edificio.jpg          → assets/foto_edificio.jpg
```

Estos archivos son necesarios para generar los PDFs de propuestas.

---

## PARTE 2 — Instalación del Frontend

### 2.1 Abrir el frontend

En una **segunda terminal** (mantén el backend corriendo en la primera):

```powershell
cd cyber-protection-ai-main\frontend
python -m http.server 5500
```

### 2.2 Acceder al sistema

Abre el navegador en:
```
http://localhost:5500/pages/login.html
```

---

## PARTE 3 — Instalación de Ollama con Gemma 3

Ollama permite generar textos de propuestas con IA local, sin internet y con total privacidad.

### 3.1 Descargar Ollama

Ve a **https://ollama.com/download** y descarga la versión para **Windows**.

Instala como cualquier programa. Al terminar, abre una terminal nueva y verifica:

```powershell
ollama --version
```

### 3.2 Descargar el modelo Gemma 3

```powershell
ollama pull gemma3:4b
```

- Tamaño de descarga: ~2.5 GB
- Con 16 GB RAM + GPU NVIDIA: funciona con aceleración
- Con 8 GB RAM sin GPU: funciona pero más lento

### 3.3 Verificar que funciona

```powershell
ollama run gemma3:4b
```

Escribe una prueba:
```
Genera una introducción de propuesta de ciberseguridad para una empresa del sector bancario en Chile.
```

Si responde en menos de 5 segundos con texto coherente, está listo.

Escribe `/bye` para salir del chat.

### 3.4 Arrancar Ollama como servicio

Antes de usar las funciones de IA en el sistema, abre una **tercera terminal** y ejecuta:

```powershell
ollama serve
```

Déjalo corriendo mientras usas el sistema.

### 3.5 Verificar integración

Ve a `http://localhost:8000/docs` en el navegador y busca el endpoint:
```
POST /proposals/generate
```

En el body usa `"usar_ia": true`. Si Ollama está corriendo, los textos serán generados por IA.

---

## PARTE 4 — Resumen de comandos diarios

Cada vez que uses el sistema necesitas tener **3 terminales abiertas**:

**Terminal 1 — Backend:**
```powershell
cd cyber-protection-ai-main
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd cyber-protection-ai-main\frontend
python -m http.server 5500
```

**Terminal 3 — Ollama (solo si usas IA):**
```powershell
ollama serve
```

---

## PARTE 5 — Funcionalidades del sistema

### Módulos disponibles

| Módulo | URL | Descripción |
|---|---|---|
| Login | /pages/login.html | Acceso al sistema |
| Dashboard | /pages/dashboard.html | Vista general |
| Clientes | /pages/clients.html | CRUD de clientes |
| Servicios | /pages/services.html | Catálogo de servicios |
| Generar Informe | /pages/report.html | Informes con IA |
| Importar Excel | /pages/import.html | Carga masiva desde Excel |
| Historial IA | /pages/ingestion.html | Importar documentos históricos |
| Usuarios | /pages/usuarios.html | Gestión de usuarios (admin) |

### Endpoints del backend

| Método | Ruta | Descripción |
|---|---|---|
| POST | /auth/login | Iniciar sesión |
| PUT | /auth/me | Actualizar perfil |
| GET/POST/PUT/DELETE | /users/ | Gestión de usuarios |
| GET/POST/PUT/DELETE | /clients/ | Gestión de clientes |
| GET/POST/PUT/DELETE | /services/ | Gestión de servicios |
| POST | /proposals/generate | Generar PDF de propuesta |
| POST | /ingestion/upload | Analizar documentos con IA |
| POST | /ingestion/confirm | Guardar datos extraídos |
| POST | /ingestion/save-logo | Guardar logo en assets |

### Documentación interactiva
```
http://localhost:8000/docs
```

---

## PARTE 6 — Solución de problemas frecuentes

### "Password cannot be longer than 72 bytes"
```powershell
pip install bcrypt==4.0.1
```

### "Form data requires python-multipart"
```powershell
pip install python-multipart
```

### "No module named 'pdfplumber'"
```powershell
pip install pdfplumber python-docx openpyxl
```

### El servidor no conecta con la BD
- Verificar que PostgreSQL está corriendo (Services en Windows)
- Verificar contraseña en `.env`
- Verificar que la BD `cyber_protection_ai` existe

### Ollama no responde
```powershell
ollama serve
# En otra terminal verificar:
ollama list
```

### Token expirado / "Invalid token"
- La sesión dura 8 horas
- Si expira, cierra sesión y vuelve a ingresar
- Si el servidor se reinició, también debes volver a iniciar sesión

### PDF no se genera
- Verificar que las imágenes están en `assets/`
- El archivo debe llamarse exactamente `logo_cyberprotection.jpg` y `foto_edificio.jpg`

---

## PARTE 7 — Arquitectura del proyecto

```
cyber-protection-ai-main/
│
├── app/                          ← Backend FastAPI
│   ├── core/                     ← Configuración, BD, seguridad
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py       ← Autenticación JWT
│   │   └── security.py           ← Hash bcrypt (fix 72 bytes)
│   │
│   ├── models/                   ← Modelos SQLAlchemy
│   │   ├── user.py               ← Usuario + Perfil + Rol
│   │   ├── client.py
│   │   └── service.py
│   │
│   ├── schemas/                  ← Validación Pydantic
│   ├── routers/                  ← Endpoints HTTP
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── client.py
│   │   ├── service.py
│   │   ├── proposal.py           ← Generación PDF
│   │   └── ingestion.py          ← Importación histórica
│   │
│   └── services/                 ← Lógica de negocio
│       ├── generate_proposal.py  ← Generador PDF corporativo
│       ├── ollama_service.py     ← IA local con Gemma 3
│       └── extractor_service.py  ← Extracción de documentos
│
├── frontend/                     ← Interfaz web
│   ├── css/                      ← Estilos
│   ├── js/                       ← Módulos JavaScript
│   └── pages/                    ← Páginas HTML
│
├── assets/                       ← Imágenes para PDFs y logos
├── propuestas_generadas/         ← PDFs generados (auto)
├── uploads_tmp/                  ← Archivos temporales (auto)
├── .env                          ← Configuración
└── requirements.txt              ← Dependencias Python
```
