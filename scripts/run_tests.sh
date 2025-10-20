#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
. .venv/bin/activate

python -m pip install --upgrade pip
if [ -f requirements-dev.txt ]; then
  pip install -r requirements-dev.txt
fi
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

pytest -q --cov=src --cov-report=xml --cov-report=term-missing
