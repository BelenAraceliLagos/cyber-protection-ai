@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul
title CyberProtection AI - Cierre de emergencia

:: ============================================================
::  HERRAMIENTA DE EMERGENCIA
::  Usar solo si start_pcp.bat no pudo cerrar correctamente
:: ============================================================

set "ROOT_DIR=%~dp0"
set "CONFIG=%ROOT_DIR%_pcp_config.ini"
set "PORT_BACK=8080"
set "PORT_FRONT=5500"

if exist "%CONFIG%" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%CONFIG%") do (
        set "key=%%A"
        set "val=%%B"
        set "key=!key: =!"
        set "val=!val: =!"
        if not "!key:~0,1!"==";" (
        if not "!key:~0,1!"=="[" (
            if "!key!"=="puerto_backend"  set "PORT_BACK=!val!"
            if "!key!"=="puerto_frontend" set "PORT_FRONT=!val!"
        ))
    )
)

echo.
echo  Forzando cierre de todos los servicios...
echo.

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT_BACK% " 2^>nul') do (
    taskkill /PID %%p /F > nul 2>&1
)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT_FRONT% " 2^>nul') do (
    taskkill /PID %%p /F > nul 2>&1
)
taskkill /IM ollama.exe /F > nul 2>&1
taskkill /IM ollama_llama_server.exe /F > nul 2>&1

echo  Servicios detenidos.
echo.
timeout /t 2 /nobreak > nul
