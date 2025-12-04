#!/usr/bin/env python3
# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/session_context_logger.py
# Finalidade: Registrar o contexto lógico (chat técnico) da sessão Garimpo ML
# Uso: Importado automaticamente pelo session_auto_end.py
# ============================================================

import os
from datetime import datetime

LOGS_DIR = "/home/ubuntu/garimpo-ml/logs"
SESSION_LOG = os.path.join(LOGS_DIR, "session_context_current.txt")

os.makedirs(LOGS_DIR, exist_ok=True)

def registrar_evento(texto: str):
    """
    Adiciona uma linha de contexto lógico ao log da sessão atual.
    Este log é incrementado a cada comando técnico importante no GPT.
    """
    if not texto.strip():
        return
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{now} UTC] {texto.strip()}\n"
    with open(SESSION_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def limpar_log_atual():
    """Zera o log atual ao iniciar uma nova sessão."""
    if os.path.exists(SESSION_LOG):
        os.remove(SESSION_LOG)
    with open(SESSION_LOG, "w", encoding="utf-8") as f:
        f.write(f"=== NOVA SESSÃO GPT INICIADA {datetime.utcnow().isoformat(timespec='seconds')}Z ===\n")


def anexar_ao_checkpoint(checkpoint_path: str):
    """
    Copia o conteúdo do log de contexto (session_context_current.txt)
    e anexa dentro do checkpoint físico (.txt) antes de encerrar.
    """
    if not os.path.exists(SESSION_LOG):
        print("⚠️ Nenhum log de contexto encontrado para anexar.")
        return

    if not os.path.exists(checkpoint_path):
        print(f"🚨 Checkpoint inexistente: {checkpoint_path}")
        return

    with open(SESSION_LOG, "r", encoding="utf-8") as f:
        contexto = f.read().strip()

    with open(checkpoint_path, "a", encoding="utf-8") as f:
        f.write("\n------------------------------------------------------------\n")
        f.write("📓 Histórico técnico detalhado da sessão:\n")
        f.write(contexto + "\n")
        f.write("------------------------------------------------------------\n")
        f.write("🔗 Checkpoint registrado e pronto para retomada\n")
        f.write("============================================================\n")

    print(f"✅ Contexto lógico anexado ao checkpoint: {os.path.basename(checkpoint_path)}")
