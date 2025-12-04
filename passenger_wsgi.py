# ============================================================
# Garimpo ML – passenger_wsgi.py (Loader mínimo do WSGI)
# ============================================================
# Função: APENAS carregar a aplicação Flask real, definida em src/app.py.
# Não registrar blueprints aqui. Não chamar .run() aqui.
# Toda a configuração de rotas/blueprints fica em /home/ubuntu/garimpo-ml/src/app.py
# ============================================================

import os
import sys

PROJECT_ROOT = "/home/ubuntu/garimpo-ml"
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

# Garantir que /home/ubuntu/garimpo-ml e /home/ubuntu/garimpo-ml/src estejam no PYTHONPATH
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Importa a instância real do Flask
# Em src/app.py: a variável é "app"
from app import app as application  # WSGI exige o nome "application"

# (Opcional) Healthcheck rápido para logs do servidor
try:
    print("[Garimpo ML] WSGI loader ativo. App importado de src/app.py")
except Exception:
    pass
