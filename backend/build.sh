#!/usr/bin/env bash
set -euo pipefail

echo "[Render Build] Using Python: $(python --version)"

echo "[Render Build] Installing backend dependencies"
pip install -r requirements.txt

echo "[Render Build] Running database migrations"
python manage.py migrate --noinput

echo "[Render Build] Collecting static files"
python manage.py collectstatic --noinput

echo "[Render Build] Done"



