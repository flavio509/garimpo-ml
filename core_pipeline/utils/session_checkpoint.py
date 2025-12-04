# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/session_checkpoint.py
# Finalidade: registrar e restaurar checkpoints de sessão do agente
# ============================================================

import os
from datetime import datetime
from core_pipeline.utils import checkpoint_registry

BASE_DIR = "/home/ubuntu/garimpo-ml/logs"
os.makedirs(BASE_DIR, exist_ok=True)

def criar_checkpoint_sessao(descricao: str = "") -> str:
    """
    Gera um checkpoint completo da sessão atual do agente Garimpo ML.
    Cria arquivo datado em /logs/ e atualiza ponteiro global.
    """
    data_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    nome = f"GARIMPOML_{data_str}_MANUAL_OK.txt"
    caminho = os.path.join(BASE_DIR, nome)

    conteudo = []
    conteudo.append("============================================================")
    conteudo.append(nome)
    conteudo.append("============================================================")
    conteudo.append(f"📅 Data/Hora UTC: {datetime.utcnow().isoformat(timespec='seconds')}Z")
    conteudo.append(f"🏗️ Ambiente: Ubuntu 24.04 LTS / Python 3.12")
    conteudo.append(f"🧠 Sessão: encerrada manualmente pelo agente Garimpo ML")
    if descricao:
        conteudo.append("------------------------------------------------------------")
        conteudo.append("📋 Descrição adicional:")
        conteudo.append(descricao.strip())
    conteudo.append("------------------------------------------------------------")
    conteudo.append("🔗 Checkpoint registrado e pronto para retomada")
    conteudo.append("============================================================")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(conteudo) + "\n")

    # Atualiza ponteiro global
    checkpoint_registry.write_pointer(caminho)
    print(f"💾 Checkpoint de sessão criado: {nome}")
    return caminho


# ============================================================
# BLOCO DE RETOMADA DE SESSÃO (LEITURA DO CHECKPOINT ATUAL)
# ============================================================

import requests
import json

def carregar_ultimo_checkpoint():
    """
    Recupera o último checkpoint físico ativo do servidor Garimpo ML.
    Faz requisição pública GET para /meuapp/session/current.
    Retorna dicionário com informações do checkpoint.
    """
    url = "https://marcasshop.com.br/meuapp/session/current"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("ok", False):
            print("⚠️ Nenhum checkpoint válido encontrado no servidor.")
            return None

        checkpoint = data.get("checkpoint", {})
        basename = checkpoint.get("basename")
        abs_path = checkpoint.get("absolute_path")

        if basename and abs_path:
            print(f"✅ Sessão retomada a partir do checkpoint {basename}.")
            print(f"🔗 Fonte: {abs_path}")
            return checkpoint
        else:
            print("⚠️ Estrutura de checkpoint inválida no JSON retornado.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"🚨 Falha ao consultar o endpoint de sessão: {e}")
        return None
    except json.JSONDecodeError:
        print("🚨 Resposta inválida (JSON corrompido).")
        return None
        