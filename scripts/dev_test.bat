@echo off
REM Ejecuta pytest con cobertura
cd /d %~dp0\..
pip install -q pytest pytest-cov
set PYTHONPATH=%CD%
pytest -q --cov=src --cov-report=term-missing
