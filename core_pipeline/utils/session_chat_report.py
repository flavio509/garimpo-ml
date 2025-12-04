# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/session_chat_report.py
# Finalidade: gerar relatório lógico do chat (estado GPT + pipeline técnico)
# ============================================================

import os
from datetime import datetime

LOG_DIR = "/home/ubuntu/garimpo-ml/logs"
os.makedirs(LOG_DIR, exist_ok=True)

def gerar_relatorio_chat(descricao: str = "", checkpoint_ativo: str = "N/A") -> str:
    """
    Gera um relatório lógico de sessão do GPT contendo:
      - Contexto técnico resumido
      - Último checkpoint ativo
      - Pendências e próximos passos
    Retorna o caminho completo do relatório gerado.
    """

    data_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    nome_arquivo = f"RELATORIO_GPT_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    caminho = os.path.join(LOG_DIR, nome_arquivo)

    conteudo = []
    conteudo.append("============================================================")
    conteudo.append(nome_arquivo)
    conteudo.append("============================================================")
    conteudo.append(f"📅 Data/Hora UTC: {data_utc}")
    conteudo.append(f"🏗️ Ambiente: Ubuntu 24.04 LTS / Flask 3.0 / Python 3.12")
    conteudo.append(f"🧠 Sessão: encerrada manualmente via comando 'encerrar Garimpo ML'")
    conteudo.append("------------------------------------------------------------")
    conteudo.append(f"📘 Checkpoint ativo: {checkpoint_ativo}")
    conteudo.append("------------------------------------------------------------")

    if descricao:
        conteudo.append("📋 Descrição adicional:")
        conteudo.append(descricao.strip())
        conteudo.append("------------------------------------------------------------")

    # Se existir log lógico atual, incorpora
    log_context = os.path.join(LOG_DIR, "session_context_current.txt")
    if os.path.exists(log_context):
        conteudo.append("🧩 Contexto lógico registrado:")
        with open(log_context, "r", encoding="utf-8") as logf:
            conteudo.append(logf.read())
        conteudo.append("------------------------------------------------------------")
    else:
        conteudo.append("⚠️ Nenhum log de contexto encontrado nesta sessão.")
        conteudo.append("------------------------------------------------------------")

    conteudo.append("📂 Estrutura de pastas principal:")
    conteudo.append("/home/ubuntu/garimpo-ml/")
    conteudo.append("├── core_pipeline/api/")
    conteudo.append("├── core_pipeline/utils/")
    conteudo.append("├── data/uploads/")
    conteudo.append("├── data/pages/")
    conteudo.append("├── out/")
    conteudo.append("└── logs/")
    conteudo.append("------------------------------------------------------------")

    conteudo.append("📊 Próximos passos sugeridos:")
    conteudo.append("1️⃣ Validar último checkpoint físico no servidor.")
    conteudo.append("2️⃣ Continuar sessão via comando: 'continuar Garimpo ML' e colar este relatório.")
    conteudo.append("3️⃣ Garantir sincronização entre checkpoints GPT e físicos.")
    conteudo.append("============================================================")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(conteudo) + "\n")

    print(f"✅ Relatório lógico do chat criado em: {caminho}")
    return caminho
