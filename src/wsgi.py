# ============================================================
# Garimpo ML – WSGI entrypoint canônico (produção)
# ============================================================
# Objetivo: Exportar "app" para o servidor WSGI (Gunicorn).
# Não registrar blueprints aqui; isso é responsabilidade de src/app.py.
# Não chamar app.run() aqui (o WSGI server faz isso).
# ============================================================

import os
import sys

PROJECT_ROOT = "/home/ubuntu/garimpo-ml"
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from app import app  # a instância Flask real fica em src/app.py

# Exposto para o WSGI server (Gunicorn espera "application")
application = app

# Log leve para auditoria (não crítico)
try:
    print("[Garimpo ML] WSGI entrypoint carregado (src/wsgi.py).")
except Exception:
    pass
