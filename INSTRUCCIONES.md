# Cyber-Protection AI — v2.0 FINAL

## Instalación desde cero

### 1. Crear venv limpio
```powershell
python -m venv venv --clear
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL
- Instalar PostgreSQL y crear la BD `cyber_protection_ai`
- El `.env` ya tiene: usuario `postgres`, contraseña `isidora`

### 3. Copiar assets de imagen a `assets/`
```
logo_cyberprotection.jpg
foto_edificio.jpg
```

### 4. Arrancar backend
```powershell
uvicorn app.main:app --reload --port 8080
```

### 5. Crear primer usuario admin (solo la primera vez)
Generar hash:
```powershell
python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print(ctx.hash('admin123'))"
```
Insertar en pgAdmin:
```sql
INSERT INTO users (name, email, hashed_password, role)
VALUES ('admin@cyberprotection.cl', 'HASH_AQUI', true);
INSERT INTO profiles (user_id, name) VALUES (1, 'Administrador');
INSERT INTO user_roles (user_id, role_id) VALUES (1, 1);
```

### 6. Arrancar frontend
```powershell
cd frontend
python -m http.server 5500
```
Abrir: http://localhost:5500/pages/login.html

---

## Cambios aplicados en esta versión

| Archivo | Cambio |
|---------|--------|
| `app/core/security.py` | ✅ Fix bcrypt "password too long" — trunca a 72 bytes |
| `requirements.txt` | ✅ Fija `bcrypt==4.0.1` compatible con passlib |
| `app/routers/service.py` | ✅ CRUD completo de servicios |
| `app/routers/proposal.py` | ✅ Generación de PDF con textos genéricos + Ollama opcional |
| `app/services/generate_proposal.py` | ✅ PDF con diseño corporativo + categorización automática |
| `frontend/js/api.js` | ✅ Puerto 8080 + proposalsAPI agregado |
| `frontend/js/services.js` | ✅ CRUD completo (reemplaza módulo en construcción) |
| `frontend/js/import_services.js` | ✅ Importador Excel con detección de duplicados |
| `frontend/pages/services.html` | ✅ CRUD completo |
| `frontend/pages/import.html` | ✅ Importador completo con drag & drop |

## Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /auth/login | Iniciar sesión |
| PUT | /auth/me | Actualizar perfil |
| GET/POST/PUT/DELETE | /users/ | Gestión de usuarios (admin) |
| GET/POST/PUT/DELETE | /clients/ | Gestión de clientes |
| GET/POST/PUT/DELETE | /services/ | Gestión de servicios |
| POST | /proposals/generate | Generar PDF → descarga directa |
| GET | /proposals/preview/{id} | Preview datos propuesta |
