# ============================================================
#  CyberProtection AI - Instalador v1.7
#  Abrir PowerShell como Administrador y ejecutar:
#  Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
#  .\install.ps1
# ============================================================

Set-StrictMode -Off
$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "    AVISO: $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "`nERROR: $msg" -ForegroundColor Red; Read-Host "Presiona Enter para salir"; exit 1 }

Clear-Host
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   CyberProtection AI - Instalador v1.7     " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# -- Verificar Administrador ---------------------------------
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Fail "Debes ejecutar este script como Administrador."
}

# -- Rutas ---------------------------------------------------
$ROOT_DIR    = Split-Path -Parent $MyInvocation.MyCommand.Path
$INSTALLERS  = Join-Path $ROOT_DIR "_instaladores"
$CONFIG_FILE = Join-Path $ROOT_DIR "_pcp_config.ini"

Write-OK "Ubicacion: $ROOT_DIR"

# -- Detectar carpeta del proyecto ---------------------------
$PROJECT_DIR = $null
$BACKEND_DIR = $null

$candidates = @(
    (Join-Path $ROOT_DIR "cyber-protection-ai-main\cyber-protection-ai-main"),
    (Join-Path $ROOT_DIR "cyber-protection-ai-main")
)

foreach ($c in $candidates) {
    if (Test-Path (Join-Path $c "backend\app")) {
        $PROJECT_DIR = $c
        $BACKEND_DIR = Join-Path $c "backend"
        break
    }
}

if (-not $PROJECT_DIR) {
    Write-Fail "No se encontro la carpeta del proyecto en $ROOT_DIR"
}

$FRONTEND_DIR = Join-Path $PROJECT_DIR "frontend"
$VENV_DIR     = Join-Path $BACKEND_DIR "venv"

Write-OK "Proyecto: $PROJECT_DIR"
Write-OK "Backend:  $BACKEND_DIR"

# -- Helpers -------------------------------------------------
function Find-Installer { param($pattern)
    if (Test-Path $INSTALLERS) {
        $f = Get-ChildItem -Path $INSTALLERS -Filter $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($f) { return $f.FullName }
    }
    return $null
}

function Test-Command { param($cmd)
    return [bool](Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path","User")
}

function Find-Python {
    $env:Path = ($env:Path -split ";" | Where-Object { $_ -notmatch "WindowsApps" }) -join ";"
    foreach ($cmd in @("py", "python", "python3")) {
        if (Test-Command $cmd) {
            $prevPref = $ErrorActionPreference
            $ErrorActionPreference = "SilentlyContinue"
            $ver = & $cmd --version 2>&1 | Out-String
            $ErrorActionPreference = $prevPref
            if ($ver -match "3\.(9|10|11|12|13)") { return $cmd }
        }
    }
    foreach ($v in @("313","312","311","310","39")) {
        foreach ($base in @("C:\Python$v", "C:\Program Files\Python$v", "C:\Program Files (x86)\Python$v")) {
            if (Test-Path "$base\python.exe") {
                $env:Path = "$base;$base\Scripts;" + $env:Path
                return "$base\python.exe"
            }
        }
    }
    return $null
}

# -- Solicitar datos -----------------------------------------
Write-Host ""
Write-Host "---------------------------------------------" -ForegroundColor DarkGray
Write-Host "  Configuracion de PostgreSQL" -ForegroundColor White
Write-Host "---------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
$PG_PASS_SEC = Read-Host "  Contrasena postgres" -AsSecureString
$PG_PASS = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($PG_PASS_SEC))
if ([string]::IsNullOrWhiteSpace($PG_PASS)) { Write-Fail "La contrasena no puede estar vacia." }

$PG_PORT = Read-Host "  Puerto PostgreSQL (Enter para usar 5432)"
if ([string]::IsNullOrWhiteSpace($PG_PORT)) { $PG_PORT = "5432" }
Write-Host ""

# ============================================================
#  1. PYTHON
# ============================================================
Write-Step "1/8 Verificando Python..."
$PYTHON_CMD = Find-Python

if ($PYTHON_CMD) {
    Write-OK "Python ya instalado: $PYTHON_CMD"
} else {
    $pyInst = Find-Installer "*python*.exe"
    if (-not $pyInst) { $pyInst = Find-Installer "*python*" }
    if ($pyInst) {
        Write-Host "    Instalando Python en silencio..." -ForegroundColor Yellow
        Start-Process $pyInst -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait
        Refresh-Path; Start-Sleep 2
    } elseif (Test-Command "winget") {
        Write-Warn "Sin instalador local. Descargando via winget..."
        winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        Refresh-Path
    } else {
        Write-Fail "No se pudo instalar Python."
    }
    $PYTHON_CMD = Find-Python
    if (-not $PYTHON_CMD) { Write-Fail "Python no encontrado tras instalacion. Reinicia e intenta de nuevo." }
    Write-OK "Python instalado: $PYTHON_CMD"
}

# ============================================================
#  2. GTK3
# ============================================================
Write-Step "2/8 Verificando GTK3..."
if (Test-Path "HKLM:\SOFTWARE\GTK3-Runtime") {
    Write-OK "GTK3 ya instalado."
} else {
    $gtkInst = Find-Installer "*gtk3*"
    if ($gtkInst) {
        Write-Host "    Instalando GTK3..." -ForegroundColor Yellow
        Start-Process $gtkInst -ArgumentList "/S" -Wait
        Write-OK "GTK3 instalado."
    } else {
        Write-Warn "GTK3 no encontrado. Los PDF pueden no generarse correctamente."
    }
}

# ============================================================
#  3. POSTGRESQL
# ============================================================
Write-Step "3/8 Verificando PostgreSQL..."
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue

if ($pgService) {
    Write-OK "PostgreSQL ya instalado: $($pgService.Name)"
    if ($pgService.Status -ne "Running") {
        Start-Service $pgService.Name
        Write-OK "Servicio iniciado."
    }
} else {
    $pgInst = Find-Installer "*postgresql*"
    if ($pgInst) {
        Write-Host "    IMPORTANTE: Cuando el instalador pida contrasena usa: $PG_PASS" -ForegroundColor Yellow
        Write-Host "                Cuando pida puerto usa: $PG_PORT" -ForegroundColor Yellow
        Read-Host "    Presiona Enter para abrir el instalador de PostgreSQL"
        Start-Process $pgInst -Wait
        Read-Host "    Presiona Enter cuando hayas terminado de instalar PostgreSQL"
    } elseif (Test-Command "winget") {
        winget install --id PostgreSQL.PostgreSQL --silent --accept-package-agreements --accept-source-agreements
    } else {
        Write-Fail "No se pudo instalar PostgreSQL."
    }
    Refresh-Path; Start-Sleep 4
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService) { Start-Service $pgService.Name -ErrorAction SilentlyContinue }
}

$PG_BIN = $null
foreach ($v in @("18","17","16","15")) {
    if (Test-Path "C:\Program Files\PostgreSQL\$v\bin\psql.exe") {
        $PG_BIN = "C:\Program Files\PostgreSQL\$v\bin"; break
    }
}
$PSQL_CMD = if ($PG_BIN) { "$PG_BIN\psql.exe" } else { "psql" }
Write-OK "psql localizado: $PSQL_CMD"

# ============================================================
#  4. OLLAMA
# ============================================================
Write-Step "4/8 Verificando Ollama..."
if (Test-Command "ollama") {
    Write-OK "Ollama ya instalado."
} else {
    $ollamaInst = Find-Installer "*ollama*"
    if ($ollamaInst) {
        Write-Host "    El instalador de Ollama se abrira ahora." -ForegroundColor Yellow
        Read-Host "    Presiona Enter para abrir el instalador de Ollama"
        Start-Process $ollamaInst
        Read-Host "    Presiona Enter cuando hayas terminado de instalar Ollama"
        Refresh-Path; Start-Sleep 3
    } elseif (Test-Command "winget") {
        winget install --id Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements
        Refresh-Path
    } else {
        Write-Fail "No se pudo instalar Ollama."
    }
    Write-OK "Ollama instalado."
}

# ============================================================
#  5. VIRTUALENV
# ============================================================
Write-Step "5/8 Creando entorno virtual Python..."
if (-not (Test-Path $VENV_DIR)) {
    & $PYTHON_CMD -m venv $VENV_DIR
    Write-OK "Virtualenv creado en: $VENV_DIR"
} else {
    Write-OK "Virtualenv ya existe."
}

$PYTHON_VENV = Join-Path $VENV_DIR "Scripts\python.exe"

# ============================================================
#  6. DEPENDENCIAS
# ============================================================
Write-Step "6/8 Instalando dependencias Python..."
$REQ_FILE = Join-Path $BACKEND_DIR "requirements.txt"
if (-not (Test-Path $REQ_FILE)) { Write-Fail "No se encontro requirements.txt en $BACKEND_DIR" }

Write-Host "    Actualizando pip..." -ForegroundColor Yellow
$prevPref = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& $PYTHON_VENV -m pip install --upgrade pip --no-input --disable-pip-version-check 2>&1 | Out-Null
Write-Host "    Instalando paquetes (puede tardar 2-5 min)..." -ForegroundColor Yellow
& $PYTHON_VENV -m pip install -r $REQ_FILE --no-input --disable-pip-version-check 2>&1 | Out-Null
$ErrorActionPreference = $prevPref
Write-OK "Dependencias instaladas."

# ============================================================
#  7. BASE DE DATOS + .ENV + MIGRACIONES
# ============================================================
Write-Step "7/8 Configurando base de datos..."
$env:PGPASSWORD = $PG_PASS

try {
    $test = & $PSQL_CMD -U postgres -h localhost -p $PG_PORT -c "\l" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Conexion fallida" }
} catch {
    Write-Fail "No se pudo conectar a PostgreSQL. Verifica que el servicio este corriendo y la contrasena sea correcta."
}

$dbExists = & $PSQL_CMD -U postgres -h localhost -p $PG_PORT -tAc "SELECT 1 FROM pg_database WHERE datname='cyber_protection_ai'" 2>&1
if ($dbExists -ne "1") {
    & $PSQL_CMD -U postgres -h localhost -p $PG_PORT -c "CREATE DATABASE cyber_protection_ai ENCODING 'UTF8';" 2>&1 | Out-Null
    Write-OK "Base de datos creada."
} else {
    Write-OK "Base de datos ya existe."
}

# Crear .env con la contrasena correcta de PostgreSQL
$ENV_FILE = Join-Path $BACKEND_DIR ".env"
$envContent = @"
DATABASE_URL=postgresql://postgres:$PG_PASS@localhost:$PG_PORT/cyber_protection_ai
SECRET_KEY=super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
"@
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ENV_FILE, $envContent, $Utf8NoBom)
Write-OK ".env creado en: $ENV_FILE"

# Aplicar migraciones - sistema simple (apply_migrations.py), sin Alembic.
# El propio script crea las tablas que falten (Base.metadata.create_all)
# y aplica los .sql pendientes de backend/migrations/, en ese orden.
$APPLY_MIGRATIONS = Join-Path $BACKEND_DIR "apply_migrations.py"
if (Test-Path $APPLY_MIGRATIONS) {
    Push-Location $BACKEND_DIR
    & $PYTHON_VENV apply_migrations.py
    Pop-Location
    Write-OK "Migraciones aplicadas."
} else {
    Write-Warn "No se encontro apply_migrations.py - el esquema de la base puede quedar incompleto."
}
$env:PGPASSWORD = ""

# ============================================================
#  8. MODELO OLLAMA
# ============================================================
Write-Step "8/8 Verificando modelo gemma3:4b..."
$ollamaProc = Start-Process "ollama" -ArgumentList "serve" -PassThru -WindowStyle Hidden
Start-Sleep 5
$prevPref = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
$modelList = & ollama list 2>&1 | Out-String
$ErrorActionPreference = $prevPref

if ($modelList -match "gemma3:4b") {
    Write-OK "Modelo ya descargado."
} else {
    Write-Host "    Descargando gemma3:4b (~3 GB). Puede tardar 10-20 minutos..." -ForegroundColor Yellow
    Write-Host "    No cierres esta ventana." -ForegroundColor Yellow
    & ollama pull gemma3:4b
    Write-OK "Modelo descargado."
}
Stop-Process -Id $ollamaProc.Id -Force -ErrorAction SilentlyContinue

# ============================================================
#  CONFIGURACION Y ACCESO DIRECTO
# ============================================================
Write-Step "Generando configuracion..."

$configContent = @"
; =============================================
;  CyberProtection AI - Configuracion Local
;  Editar con el Bloc de Notas si es necesario
; =============================================

[proyecto]
ruta_proyecto = $PROJECT_DIR
backend_dir   = $BACKEND_DIR

[postgresql]
password     = $PG_PASS
puerto       = $PG_PORT
base_datos   = cyber_protection_ai
usuario      = postgres

[servidor]
puerto_backend  = 8080
puerto_frontend = 5500

[ollama]
modelo = gemma3:4b
"@
[System.IO.File]::WriteAllText($CONFIG_FILE, $configContent, $Utf8NoBom)
Write-OK "Configuracion guardada: $CONFIG_FILE"

$DESKTOP       = [Environment]::GetFolderPath("Desktop")
$START_BAT     = Join-Path $ROOT_DIR "start_pcp.bat"
$SHORTCUT_PATH = Join-Path $DESKTOP "CyberProtection AI.lnk"
$WshShell      = New-Object -ComObject WScript.Shell
$Shortcut      = $WshShell.CreateShortcut($SHORTCUT_PATH)
$Shortcut.TargetPath       = "cmd.exe"
$Shortcut.Arguments        = "/c `"$START_BAT`""
$Shortcut.WorkingDirectory = $ROOT_DIR
$Shortcut.Description      = "Iniciar CyberProtection AI"
$ICO_PATH = Join-Path $PROJECT_DIR "assets\favicon.ico"
if (Test-Path $ICO_PATH) { $Shortcut.IconLocation = $ICO_PATH }
$Shortcut.Save()
Write-OK "Acceso directo creado en el escritorio."

# -- Fin -----------------------------------------------------
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "   Instalacion completada con exito          " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  -> Doble-clic en 'CyberProtection AI' en el escritorio" -ForegroundColor White
Write-Host "  -> Para cerrar el sistema: presiona cualquier tecla en la ventana" -ForegroundColor White
Write-Host "  -> Para cambiar contrasena de BD: edita _pcp_config.ini y .env" -ForegroundColor White
Write-Host "  -> Para agregar cambios de esquema nuevos: backend\migrations\README.md" -ForegroundColor White
Write-Host ""
Read-Host "Presiona Enter para cerrar"
