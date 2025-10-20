@echo off
REM Ejecuta ruff y black --check
cd /d %~dp0\..
pip install -q ruff black
ruff check src tests
black --check src tests
