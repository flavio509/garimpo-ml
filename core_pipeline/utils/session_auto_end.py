#!/usr/bin/env python3
# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/session_auto_end.py
# Finalidade: Encerrar sessão Garimpo ML automaticamente
# Uso: python3 core_pipeline/utils/session_auto_end.py "descrição opcional"
# ============================================================

import sys
import os
sys.path.append("/home/ubuntu/garimpo-ml")

import os
import sys
import requests
from datetime import datetime
import subprocess
import json

# ------------------------------------------------------------
# CONFIGURAÇÕES FIXAS
# ------------------------------------------------------------
LOGS_DIR = "/home/ubuntu/garimpo-ml/logs"
SESSION_URL = "https://marcasshop.com.br/meuapp/session/encerrar"
TOKEN = "ML_TOKEN_2025_ABC12345"  # ⚠️ manter sincronizado com o ambiente

# ------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------
def encerrar_sessao(descricao: str = ""):
    """Encerra a sessão no servidor e exibe o comando GPT pronto."""
    payload = {"observacoes": descricao or "Encerramento automático via script Garimpo ML"}
    headers = {"X-GM-Token": TOKEN, "Content-Type": "application/json"}

    print("============================================================")
    print("🧩 Garimpo ML — Encerramento Automático de Sessão")
    print(f"🕒 {datetime.utcnow().isoformat(timespec='seconds')}Z")
    print("============================================================")

    try:
        response = requests.post(SESSION_URL, headers=headers, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"🚨 Falha HTTP {response.status_code}: {response.text}")
            return

        data = response.json()
        if not data.get("ok"):
            print(f"⚠️ Erro: {data}")
            return

        checkpoint = os.path.basename(data.get("checkpoint", ""))
        relatorio = data.get("relatorio", "")
        gpt_pointer = data.get("gpt_pointer", "")

        print(f"✅ Sessão encerrada com sucesso!")
        print(f"📄 Relatório: {relatorio}")
        print(f"💾 Checkpoint: {checkpoint}")
        print(f"📘 Ponteiro GPT: {gpt_pointer}")

        # Executa o gptsync automaticamente
        helper_path = "/home/ubuntu/garimpo-ml/core_pipeline/utils/gpt_sync_helper.py"
        if os.path.exists(helper_path):
            print("------------------------------------------------------------")
            print("🔄 Executando sincronização GPT (gptsync)...\n")
            subprocess.run(["python3", helper_path])
        else:
            print("⚠️ gpt_sync_helper.py não encontrado, sincronização manual necessária.")

    except requests.exceptions.RequestException as e:
        print(f"🚨 Falha ao comunicar com o endpoint: {e}")
    except json.JSONDecodeError:
        print("🚨 Resposta inválida (JSON corrompido).")

    # Anexa o histórico lógico da sessão ao checkpoint
    try:
        from core_pipeline.utils import session_context_logger
        session_context_logger.anexar_ao_checkpoint(data.get("checkpoint"))
    except Exception as e:
        print(f"⚠️ Falha ao anexar contexto lógico: {e}")

    from core_pipeline.utils.session_chat_report import gerar_relatorio_chat

    # Após gerar o checkpoint físico
    from core_pipeline.utils.session_chat_report import gerar_relatorio_chat

    # Extrai o nome do arquivo base do checkpoint físico
    checkpoint_basename = os.path.basename(checkpoint_path) if "checkpoint_path" in locals() else "N/A"

    # Gera relatório lógico do chat
    relatorio_path = gerar_relatorio_chat(
        descricao="Encerramento automático da sessão Garimpo ML",
        checkpoint_ativo=checkpoint_basename
    )
    print(f"🧾 Relatório lógico gerado: {relatorio_path}")


    print("============================================================")
    print("✅ Processo concluído.")
    print("============================================================")


if __name__ == "__main__":
    descricao = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    encerrar_sessao(descricao)
