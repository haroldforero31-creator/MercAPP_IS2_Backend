#!/usr/bin/env bash
set -o errexit
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p uploads/products uploads/categories uploads/invoices
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Base de datos inicializada correctamente.')
"
