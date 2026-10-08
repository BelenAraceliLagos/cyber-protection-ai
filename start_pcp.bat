@echo off
setlocal enabledelayedexpansion
title CyberProtection AI

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%cyber-protection-ai-main\backend"
set "FRONTEND_DIR=%ROOT_DIR%cyber-protection-ai-main\frontend"
set "BACKUPS_DIR=%ROOT_DIR%_backups"
set "CONFIG_FILE=%ROOT_DIR%_pcp_config.ini"
set "VENV_PYTHON=%BACKEND_DIR%\venv\Scripts\python.exe"
set "PORT_BACK=8080"
set "PORT_FRONT=5500"

cls
echo.
echo  =============================================
echo    CyberProtection AI
echo  =============================================
echo.

if not exist "%VENV_PYTHON%" (
    echo  [ERROR] Entorno virtual no encontrado.
    echo  Ruta buscada: %VENV_PYTHON%
    echo.
    echo  Si es la primera vez que instalas en este equipo, corre
    echo  install.ps1 primero.
    timeout /t 8 /nobreak > nul
    exit /b 1
)

if not exist "%CONFIG_FILE%" (
    echo  [ERROR] No se encontro _pcp_config.ini
    echo  Corre install.ps1 primero para generar la configuracion.
    timeout /t 8 /nobreak > nul
    exit /b 1
)

"%VENV_PYTHON%" "%BACKEND_DIR%\read_config.py" "%CONFIG_FILE%" > "%TEMP%\pcp_config_vars.txt" 2>"%TEMP%\pcp_config_err.txt"
for /f "tokens=1,* delims==" %%A in (%TEMP%\pcp_config_vars.txt) do (
    set "%%A=%%B"
)
set "PGPASSWORD=%PG_PASS%"

if "%PG_PASS%"=="" (
    echo  [ERROR] No se pudo leer la contrasena desde _pcp_config.ini
    echo.
    echo  Salida de read_config.py:
    type "%TEMP%\pcp_config_vars.txt" 2>nul
    echo.
    echo  Errores de read_config.py:
    type "%TEMP%\pcp_config_err.txt" 2>nul
    echo.
    timeout /t 20 /nobreak > nul
    exit /b 1
)
del "%TEMP%\pcp_config_vars.txt" > nul 2>&1
del "%TEMP%\pcp_config_err.txt" > nul 2>&1

set "PG_BIN="
for %%V in (18 17 16 15) do (
    if exist "C:\Program Files\PostgreSQL\%%V\bin\psql.exe" (
        if "%PG_BIN%"=="" set "PG_BIN=C:\Program Files\PostgreSQL\%%V\bin"
    )
)

if not exist "%BACKUPS_DIR%" mkdir "%BACKUPS_DIR%"

echo  [1/6] Verificando PostgreSQL...
powershell -NoProfile -Command "Get-Service postgresql* | Where-Object {$_.Status -ne 'Running'} | Start-Service" > nul 2>&1
timeout /t 2 /nobreak > nul
echo         OK

echo  [2/6] Verificando backup...
set "LATEST_BACKUP="
for /f "delims=" %%F in ('dir /b /o-d "%BACKUPS_DIR%\*.dump" 2^>nul') do (
    if "!LATEST_BACKUP!"=="" set "LATEST_BACKUP=%%F"
)
if "!LATEST_BACKUP!"=="" (
    echo         Sin backups previos, omitiendo.
    goto SKIP_RESTORE
)

set "TABLE_COUNT=0"
"%PG_BIN%\psql.exe" -U %PG_USER% -h localhost -p %PG_PORT% -d %PG_DB% -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" > "%TEMP%\tc.txt" 2>nul
set /p TABLE_COUNT=<"%TEMP%\tc.txt"
del "%TEMP%\tc.txt" > nul 2>&1

if !TABLE_COUNT! LSS 5 (
    echo         BD nueva detectada, restaurando !LATEST_BACKUP!...
    "%PG_BIN%\pg_restore.exe" -U %PG_USER% -h localhost -p %PG_PORT% -d %PG_DB% --clean --if-exists "%BACKUPS_DIR%\!LATEST_BACKUP!" > "%ROOT_DIR%_restore.log" 2>&1
    echo         OK - datos restaurados
) else (
    echo         BD existente con datos, omitiendo restauracion.
)
:SKIP_RESTORE

echo  [3/6] Aplicando migraciones pendientes...
pushd "%BACKEND_DIR%"
"%VENV_PYTHON%" apply_migrations.py
popd
echo         OK

echo  [4/6] Iniciando Ollama...
curl -s http://localhost:11434 > nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -WindowStyle Hidden -Command "Start-Process 'ollama' -ArgumentList 'serve' -WindowStyle Hidden"
    powershell -NoProfile -Command "for ($i=0; $i -lt 20; $i++) { Start-Sleep 2; try { Invoke-WebRequest http://localhost:11434 -TimeoutSec 2 -ErrorAction Stop | Out-Null; break } catch {} }"
)
echo         OK

echo  [5/6] Iniciando Backend...
set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\ucrt64\bin
netstat -ano | findstr ":%PORT_BACK% " > nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -WindowStyle Hidden -Command "Start-Process '%VENV_PYTHON%' -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','%PORT_BACK%' -WorkingDirectory '%BACKEND_DIR%' -WindowStyle Hidden"
    powershell -NoProfile -Command "for ($i=0; $i -lt 30; $i++) { Start-Sleep 2; try { Invoke-WebRequest http://localhost:%PORT_BACK%/health -TimeoutSec 2 -ErrorAction Stop | Out-Null; break } catch {} }"
) else (
    echo         Puerto %PORT_BACK% ya en uso, verificando salud...
    powershell -NoProfile -Command "try { Invoke-WebRequest http://localhost:%PORT_BACK%/health -TimeoutSec 3 -ErrorAction Stop | Out-Null } catch { Write-Host 'Backend no responde, reiniciando...'; Get-NetTCPConnection -LocalPort %PORT_BACK% | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Start-Sleep 2; Start-Process '%VENV_PYTHON%' -ArgumentList '-m','uvicorn','app.main:app','--host','0.0.0.0','--port','%PORT_BACK%' -WorkingDirectory '%BACKEND_DIR%' -WindowStyle Hidden; for ($i=0; $i -lt 30; $i++) { Start-Sleep 2; try { Invoke-WebRequest http://localhost:%PORT_BACK%/health -TimeoutSec 2 -ErrorAction Stop | Out-Null; break } catch {} } }"
)
echo         OK - Puerto %PORT_BACK%

echo  [6/6] Iniciando Frontend...
netstat -ano | findstr ":%PORT_FRONT% " > nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -WindowStyle Hidden -Command "Start-Process '%VENV_PYTHON%' -ArgumentList '-m','http.server','%PORT_FRONT%' -WorkingDirectory '%FRONTEND_DIR%' -WindowStyle Hidden"
    timeout /t 2 /nobreak > nul
)
echo         OK - Puerto %PORT_FRONT%

echo.
echo  =============================================
echo    Sistema listo
echo  =============================================
echo.
echo  Acceso: http://localhost:%PORT_FRONT%/pages/login.html
echo.
echo  Presiona cualquier tecla para CERRAR el sistema
echo.

timeout /t 2 /nobreak > nul
start "" "http://localhost:%PORT_FRONT%/pages/login.html"

pause > nul

echo.
echo  Cerrando sistema...
echo.

echo  [1/2] Guardando backup...
for /f "delims=" %%D in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm'"') do set "BACKUP_NAME=backup_%%D.dump"
"%PG_BIN%\pg_dump.exe" -U %PG_USER% -h localhost -p %PG_PORT% -d %PG_DB% -F c -f "%BACKUPS_DIR%\%BACKUP_NAME%" > "%ROOT_DIR%_backup.log" 2>&1
set "COUNT=0"
for /f "delims=" %%F in ('dir /b /o-d "%BACKUPS_DIR%\*.dump" 2^>nul') do (
    set /a COUNT+=1
    if !COUNT! gtr 7 del "%BACKUPS_DIR%\%%F" > nul 2>&1
)
echo         OK - %BACKUP_NAME%

echo  [2/2] Deteniendo servicios...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT_BACK% " 2^>nul') do taskkill /PID %%p /F > nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT_FRONT% " 2^>nul') do taskkill /PID %%p /F > nul 2>&1
taskkill /IM ollama.exe /F > nul 2>&1
taskkill /IM ollama_llama_server.exe /F > nul 2>&1
echo         OK

echo.
echo  Sistema cerrado correctamente.
timeout /t 3 /nobreak > nul
