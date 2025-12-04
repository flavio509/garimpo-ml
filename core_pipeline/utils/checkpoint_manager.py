import os
from datetime import datetime

# ============================================================
# Arquivo: /home/ubuntu/garimpo-ml/core_pipeline/utils/checkpoint_manager.py
# Ação: Alterar — atualizar ponteiro global após gerar checkpoint
# ============================================================

class CheckpointManager:
    """
    Gerencia checkpoints automáticos do Garimpo ML.
    Cria GarimpoML_AUTO_[data].txt a cada 3 micro-passos confirmados.
    """

    BASE_DIR = "/home/ubuntu/garimpo-ml/logs/"
    CHECKPOINT_PREFIX = "GarimpoML_AUTO_"
    MICROSTEP_TRIGGER = 3

    def __init__(self):
        self.microstep_count = 0
        os.makedirs(self.BASE_DIR, exist_ok=True)

    def registrar_micro_passo(self, arquivo: str, acao: str, resultado: str, proximo: str):
        """Registra micro-passo e gera checkpoint automático a cada 3 confirmações."""
        self.microstep_count += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"Data/Hora: {now}\n"
            f"Arquivo: {arquivo}\n"
            f"Ação: {acao}\n"
            f"Resultado: {resultado}\n"
            f"Próximo passo: {proximo}\n"
            f"---\n"
        )
        session_log = os.path.join(self.BASE_DIR, "Relatorio_Sessao_Atual.txt")
        with open(session_log, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Gera checkpoint automático a cada 3 micro-passos confirmados
        if self.microstep_count % self.MICROSTEP_TRIGGER == 0:
            self._gerar_checkpoint_auto()

    def _gerar_checkpoint_auto(self):
        """Cria arquivo de checkpoint automático e atualiza ponteiro global."""
        date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"{self.CHECKPOINT_PREFIX}{date_str}_AUTO_OK.txt"
        filepath = os.path.join(self.BASE_DIR, filename)

        # Criação do checkpoint
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Checkpoint automático gerado em {datetime.now()}\n")
            f.write("Estado: AUTO_OK\n")

        print(f"💾 Checkpoint automático gerado: {filename}")

        # Atualiza ponteiro global
        try:
            from core_pipeline.utils import checkpoint_registry
            checkpoint_registry.write_pointer(filepath)
            print(f"🔗 Ponteiro global atualizado → {filename}")
        except Exception as e:
            print(f"⚠️ Falha ao atualizar ponteiro global: {e}")

# Instância global
checkpoint_manager = CheckpointManager()
