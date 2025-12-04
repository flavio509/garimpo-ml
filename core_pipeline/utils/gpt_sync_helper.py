#!/usr/bin/env python3
# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/src/core_pipeline/utils/gpt_sync_helper.py
# Finalidade: sincronizar checkpoint físico ↔ GPT (manual)
# Uso: python3 src/core_pipeline/utils/gpt_sync_helper.py
# ============================================================

import os
from datetime import datetime

LOGS_DIR = "/home/ubuntu/garimpo-ml/logs"
GPT_POINTER = os.path.join(LOGS_DIR, "LATEST_CHECKPOINT_GPT.txt")
MAIN_POINTER = os.path.join(LOGS_DIR, "LATEST_CHECKPOINT.txt")

def ler_arquivo(caminho):
    """Lê o conteúdo de um arquivo de texto, se existir."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def main():
    print("============================================================")
    print("🔄 Garimpo ML — Utilitário de Sincronização GPT")
    print(f"🕒 {datetime.utcnow().isoformat(timespec='seconds')}Z")
    print("============================================================")

    gpt_cp = ler_arquivo(GPT_POINTER)
    main_cp = ler_arquivo(MAIN_POINTER)

    if not gpt_cp and not main_cp:
        print("⚠️ Nenhum checkpoint encontrado em /logs/.")
        print("   Execute 'encerrar Garimpo ML' para gerar um novo checkpoint.")
        return

    if gpt_cp:
        print(f"📘 Ponteiro GPT: {gpt_cp}")
    if main_cp:
        print(f"📗 Ponteiro físico: {os.path.basename(main_cp)}")

    ativo = gpt_cp or os.path.basename(main_cp)
    print("------------------------------------------------------------")
    print("➡️ Copie o comando abaixo e cole no GPT:")
    print()
    print(f"continuar Garimpo ML\ncheckpoint: {ativo}")
    print()
    print("------------------------------------------------------------")
    print("✅ Sincronização concluída.")
    print("============================================================")

if __name__ == "__main__":
    main()
