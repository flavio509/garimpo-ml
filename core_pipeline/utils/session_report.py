# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/session_report.py
# Finalidade: gerar relatório técnico completo ao encerrar Garimpo ML
# ============================================================

import os
from datetime import datetime
from core_pipeline.utils import session_checkpoint, checkpoint_registry

LOGS_DIR = "/home/ubuntu/garimpo-ml/logs"
os.makedirs(LOGS_DIR, exist_ok=True)

def gerar_relatorio_sessao(modulos_ativos=None, arquivos_modificados=None, observacoes=None):
    """
    Gera relatório completo da sessão no formato:
    /logs/Relatorio_Sessao_[data].txt
    Inclui: data/hora, checkpoint, módulos e observações.
    """
    data_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"Relatorio_Sessao_{data_str}.txt"
    caminho = os.path.join(LOGS_DIR, nome_arquivo)

    checkpoint_atual = checkpoint_registry.read_pointer()

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("============================================================\n")
        f.write("RELATÓRIO DE SESSÃO — GARIMPO ML\n")
        f.write("============================================================\n")
        f.write(f"📅 Data/Hora UTC: {datetime.utcnow().isoformat(timespec='seconds')}Z\n")
        f.write(f"🧩 Checkpoint ativo: {checkpoint_atual.get('basename')}\n")
        f.write(f"📂 Caminho: {checkpoint_atual.get('absolute_path')}\n")
        f.write(f"------------------------------------------------------------\n")

        if modulos_ativos:
            f.write("🔧 Módulos ativos:\n")
            for m in modulos_ativos:
                f.write(f"   • {m}\n")
            f.write("------------------------------------------------------------\n")

        if arquivos_modificados:
            f.write("📝 Arquivos modificados nesta sessão:\n")
            for a in arquivos_modificados:
                f.write(f"   • {a}\n")
            f.write("------------------------------------------------------------\n")

        if observacoes:
            f.write("💬 Observações:\n")
            f.write(observacoes.strip() + "\n")
            f.write("------------------------------------------------------------\n")

        f.write("🔗 Checkpoint de encerramento criado.\n")
        f.write("============================================================\n")

    print(f"🧾 Relatório de sessão gerado: {nome_arquivo}")
    return caminho


def rotina_encerramento(modulos_ativos=None, arquivos_modificados=None, observacoes=None):
    """
    Executa o encerramento completo:
    1️⃣ Gera checkpoint manual
    2️⃣ Atualiza ponteiro global
    3️⃣ Cria relatório técnico
    """
    # Cria checkpoint de sessão
    caminho_ckpt = session_checkpoint.criar_checkpoint_sessao("Encerramento de sessão completo.")
    # Gera relatório vinculado
    caminho_relatorio = gerar_relatorio_sessao(
        modulos_ativos=modulos_ativos,
        arquivos_modificados=arquivos_modificados,
        observacoes=observacoes
    )

    print("✅ Sessão encerrada com sucesso.")
    print(f"📄 Relatório: {caminho_relatorio}")
    print(f"💾 Checkpoint: {caminho_ckpt}")
    print("============================================================")
    return {"checkpoint": caminho_ckpt, "relatorio": caminho_relatorio}
