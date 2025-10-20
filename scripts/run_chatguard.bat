@echo off
REM Lanza los conectores de ChatGuard (este repo) en ventanas separadas.
REM Usa el Python por defecto del sistema o del venv activado en esta consola.

setlocal ENABLEDELAYEDEXPANSION
set ROOT=%~dp0..
cd /d "%ROOT%"

REM Opcional: aumentar logs
REM set LOG_LEVEL=info

REM Verificar que requirements estén instalados en tu entorno actual
REM python -m pip install -r requirements.txt

start "ChatGuard - Telegram" cmd /k "python src\connectors\telegram_polling.py"
start "ChatGuard - Discord"  cmd /k "python src\connectors\discord_connector.py"

echo Procesos de ChatGuard lanzados desde: %ROOT%
pause
