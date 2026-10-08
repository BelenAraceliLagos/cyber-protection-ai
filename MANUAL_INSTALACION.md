# CyberProtection AI — Manual de Instalación

**Versión 1.2 — Junio 2026**

---

## Estructura de carpetas

Coloca todos los archivos así, **en la misma carpeta madre** (puede estar en cualquier ruta):

```
📁 [Cualquier carpeta]/
├── 📁 cyber-protection-ai-main/    ← código del proyecto
├── 📁 _instaladores/               ← instaladores de aplicaciones
│   ├── instalador de python.org.msix
│   ├── instalador de postgresql.org.exe
│   ├── instalador de ollama.com.exe
│   └── gtk3-runtime-x.xx.exe
├── install.ps1
├── start_pcp.bat
├── stop_pcp.bat
└── MANUAL_INSTALACION.md
```

> Los scripts detectan su ubicación automáticamente.
> No importa en qué disco o carpeta estén.

---

## Aplicaciones requeridas en `_instaladores/`

| Aplicación | Para qué sirve | Dónde descargar |
|---|---|---|
| **Python 3.12** | Lenguaje base | https://python.org/downloads |
| **PostgreSQL 18** | Base de datos | https://postgresql.org/download/windows |
| **Ollama** | Motor de IA local | https://ollama.com/download/windows |
| **GTK3 Runtime** | Generación de PDF | https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases |

No es necesario renombrar los archivos.

---

## Paso 1 — Reemplazar main.py

Copia el `main.py` incluido a:
```
cyber-protection-ai-main/backend/app/main.py
```
Reemplaza el archivo existente.

---

## Paso 2 — Instalar (solo una vez)

1. Click derecho sobre `install.ps1` → **"Ejecutar con PowerShell"**
2. Si Windows pregunta si deseas permitir cambios → **Sí**
3. Ingresa la contraseña que usarás para PostgreSQL
4. Ingresa el puerto (Enter para usar 5432)

El instalador hace todo automáticamente. Solo debes intervenir en:

- **Python (.msix):** Aparece una ventana — completa la instalación y vuelve a la ventana negra y presiona Enter
- **PostgreSQL:** El instalador te recordará la contraseña a usar antes de abrir su ventana
- **Modelo de IA (~3 GB):** Puede tardar 10–20 minutos — no cierres la ventana

Al terminar crea un acceso directo **"CyberProtection AI"** en el escritorio.

---

## Uso diario

### Iniciar
**Doble-clic en "CyberProtection AI"** en el escritorio.

La ventana mostrará el progreso:
```
[1/6] Verificando PostgreSQL...     OK
[2/6] Actualizando base de datos... OK
[3/6] Verificando backup...         OK
[4/6] Iniciando Ollama...           OK
[5/6] Iniciando Backend...          OK - Puerto 8080
[6/6] Iniciando Frontend...         OK - Puerto 5500

Acceso: http://localhost:5500/pages/login.html
Presiona cualquier tecla para CERRAR el sistema
```

El navegador se abre automáticamente. La ventana negra debe permanecer abierta mientras usas el sistema.

### Cerrar
Cuando termines de trabajar, haz clic en la ventana negra y **presiona cualquier tecla**.

El sistema guardará automáticamente un backup antes de cerrar todo.

---

## Cambiar la contraseña de PostgreSQL

1. Abre `_pcp_config.ini` con el **Bloc de Notas**
2. Cambia la línea `password = tu_contraseña`
3. Guarda el archivo

---

## Backups

Los backups se guardan en `_backups/` dentro de la carpeta madre.
Se mantienen los últimos 7 automáticamente — los más antiguos se eliminan solos.

---

## Si algo falla

**La ventana se cerró sin hacer backup:**
Ejecuta `stop_pcp.bat` (herramienta de emergencia, no hace backup).

**"No se puede ejecutar scripts" al abrir install.ps1:**
Abre PowerShell como Administrador y ejecuta:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**El navegador abre pero no carga:**
Espera 20 segundos y recarga la página.

**Error 503 al generar propuestas PDF:**
Ollama necesita al menos 8 GB de RAM disponibles. Cierra otras aplicaciones.

**Los PDF no se generan:**
GTK3 puede no estar instalado. Instálalo manualmente desde `_instaladores/`.

---

**Cyber-Protection — Servicio Técnico Gamer Chile SPA**
La Capitanía 80, oficina 108, Las Condes, Santiago
