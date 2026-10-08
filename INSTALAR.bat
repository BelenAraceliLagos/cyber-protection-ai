@echo off
:: CyberProtection AI - Instalador
:: Doble-clic para instalar

:: Verificar administrador y elevar si es necesario
net session >nul 2>&1
if errorlevel 1 (
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs -WorkingDirectory '%~dp0'"
    exit /b
)

:: Ejecutar instalador PowerShell con bypass directo
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
