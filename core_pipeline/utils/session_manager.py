# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/session_manager.py
# Ação: Correção de caminho base (core_pipeline na raiz)
# ============================================================

import os
import glob
from datetime import datetime

# Diretórios de checkpoint
CHECKPOINT_DIRS = [
    "/home/ubuntu/garimpo-ml/backups/",
    "/home/ubuntu/garimpo-ml/logs/"
]

def get_latest_checkpoint():
    """
    Retorna o caminho completo do checkpoint mais recente (manual ou automático).
    """
    candidates = []
    for d in CHECKPOINT_DIRS:
        for path in glob.glob(os.path.join(d, "GarimpoML_*.txt")):
            mtime = os.path.getmtime(path)
            candidates.append((path, mtime))

    if not candidates:
        return None

    latest = max(candidates, key=lambda x: x[1])[0]
    return latest


def load_latest_checkpoint():
    """
    Carrega o conteúdo do checkpoint mais recente e retorna como string.
    """
    latest = get_latest_checkpoint()
    if not latest:
        return "Nenhum checkpoint encontrado."

    with open(latest, "r", encoding="utf-8") as f:
        data = f.read()

    print(f"[Garimpo ML] Checkpoint restaurado automaticamente: {os.path.basename(latest)}")
    print("=" * 60)
    print(os.path.basename(latest).replace(".txt", "").upper())
    print("=" * 60)
    print(data)
    return data


if __name__ == "__main__":
    # Execução direta para teste
    load_latest_checkpoint()
