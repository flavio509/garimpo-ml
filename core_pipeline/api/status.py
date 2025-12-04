# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/src/core_pipeline/api/status.py
# Ação: Criar — Blueprint de status e checkpoint ativo
# ============================================================

from flask import Blueprint, jsonify
from datetime import datetime
import platform
import os

from core_pipeline.utils import checkpoint_registry

status_bp = Blueprint("status", __name__, url_prefix="/meuapp")

@status_bp.route("/status", methods=["GET"])
def get_status():
    """Retorna informações do estado atual do Garimpo ML."""
    pointer = checkpoint_registry.read_pointer()
    data = {
        "ok": True,
        "message": "Garimpo ML ativo",
        "checkpoint_atual": pointer.get("basename"),
        "checkpoint_path": pointer.get("absolute_path"),
        "checkpoint_timestamp": pointer.get("timestamp_utc"),
        "server_time": datetime.utcnow().isoformat() + "Z",
        "python_version": platform.python_version(),
        "cwd": os.getcwd(),
    }
    return jsonify(data), 200

@status_bp.route("/checkpoint/refresh", methods=["POST", "GET"])
def refresh_checkpoint():
    """Força atualização do ponteiro para o checkpoint mais recente."""
    pointer = checkpoint_registry.refresh_pointer()
    data = {
        "ok": True,
        "message": "Ponteiro de checkpoint atualizado",
        "checkpoint_atual": pointer.get("basename"),
        "checkpoint_timestamp": pointer.get("timestamp_utc"),
    }
    return jsonify(data), 200
