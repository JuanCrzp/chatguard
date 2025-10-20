@echo off
REM Formatea con black y corrige con ruff
cd /d %~dp0\..
pip install -q ruff black
ruff check --fix src tests
black src tests
