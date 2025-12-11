#!/usr/bin/env bash
# Script de build para Render

set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Collectstatic
python manage.py collectstatic --noinput

# Aplicar migraciones
python manage.py migrate
