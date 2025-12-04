# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/checkpoint_registry.py
# Finalidade: fonte única da verdade do "último checkpoint"
# ============================================================

import os
import glob
import re
from datetime import datetime

BACKUPS_DIR = "/home/ubuntu/garimpo-ml/backups"
LOGS_DIR    = "/home/ubuntu/garimpo-ml/logs"
POINTER     = os.path.join(LOGS_DIR, "LATEST_CHECKPOINT.txt")

# Padrões aceitos (maiusc./minusc. e AUTO)
PATTERNS = [
    "GarimpoML_*.txt",
    "GARIMPOML_*.txt",
    "GarimpoML_AUTO_*.txt",
    "GARIMPOML_AUTO_*.txt",
]

# Segurança: só considera arquivos no padrão esperado
_SAFE_NAME_RX = re.compile(r"^(?:GarimpoML|GARIMPOML)_(?:AUTO_)?\d{8,}.*\.txt$")

def _iter_paths():
    """Itera por backups/logs devolvendo caminhos candidatos."""
    for d in (BACKUPS_DIR, LOGS_DIR):
        if not os.path.isdir(d):
            continue
        for pattern in PATTERNS:
            for path in glob.glob(os.path.join(d, pattern)):
                yield path

def _list_candidates():
    """Retorna [(path, mtime)] de checkpoints válidos."""
    candidates = []
    for path in _iter_paths():
        base = os.path.basename(path)
        if not _SAFE_NAME_RX.match(base):
            continue
        try:
            mtime = os.path.getmtime(path)
            candidates.append((path, mtime))
        except FileNotFoundError:
            continue
    return candidates

def find_latest_checkpoint_path():
    """Retorna caminho do checkpoint mais recente ou None."""
    candidates = _list_candidates()
    if not candidates:
        return None
    latest_path = max(candidates, key=lambda x: x[1])[0]
    return latest_path

def write_pointer(latest_path: str) -> str:
    """
    Grava LATEST_CHECKPOINT.txt com:
      - timestamp_utc
      - absolute_path
      - basename
    Retorna o conteúdo gravado.
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    base = os.path.basename(latest_path) if latest_path else "NONE"
    content = (
        "GARIMPO_ML_CHECKPOINT_POINTER\n"
        f"timestamp_utc={ts}\n"
        f"absolute_path={latest_path or 'NONE'}\n"
        f"basename={base}\n"
    )
    with open(POINTER, "w", encoding="utf-8") as f:
        f.write(content)
    return content

def read_pointer() -> dict:
    """
    Lê LATEST_CHECKPOINT.txt. Se não existir, cria a partir do mais recente disponível.
    Retorna: {'absolute_path', 'basename', 'timestamp_utc'}
    """
    if not os.path.exists(POINTER):
        latest = find_latest_checkpoint_path()
        if latest:
            write_pointer(latest)
        else:
            return {"absolute_path": None, "basename": None, "timestamp_utc": None}

    data = {"absolute_path": None, "basename": None, "timestamp_utc": None}
    try:
        with open(POINTER, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines()]
        for ln in lines:
            if ln.startswith("absolute_path="):
                data["absolute_path"] = ln.split("=", 1)[1]
            elif ln.startswith("basename="):
                data["basename"] = ln.split("=", 1)[1]
            elif ln.startswith("timestamp_utc="):
                data["timestamp_utc"] = ln.split("=", 1)[1]
    except Exception:
        pass
    return data

def refresh_pointer() -> dict:
    """
    Força atualização do ponteiro para o checkpoint mais recente e retorna o dict atualizado.
    """
    latest = find_latest_checkpoint_path()
    if latest:
        write_pointer(latest)
    return read_pointer()
