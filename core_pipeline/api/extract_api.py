"""
Garimpo ML – API de Extração de Produtos (v2025-11-24)
------------------------------------------------------
Rota HTTP responsável por disparar o pipeline de extração de produtos
a partir dos OCR JSONs gerados para um job.

Fluxo:
    /extract?job_id=<ID>

Chama:
    pipeline_extract_products.run(job_id)
    
Retorno:
    JSON contendo:
        - ok: True/False
        - job_id
        - output_file: caminho do arquivo gerado
        - products_count: quantidade de produtos extraídos
"""

import os
import json
from flask import Blueprint, request, jsonify

# Importação interna do pipeline recém-criado
from core_pipeline.api.pipeline_extract_products import run as run_extract_pipeline

# ============================================================
# 🔹 Blueprint
# ============================================================
extract_bp = Blueprint("extract_bp", __name__, url_prefix="/meuapp/extract-api")

# ============================================================
# 🔹 ROTA: /extract
# ============================================================
@extract_bp.route("/extract", methods=["GET", "POST"])
def extract_products():
    """
    Dispara o pipeline de extração de produtos para um job específico.

    Parâmetros aceitos:
        - job_id via GET ou POST JSON

    Exemplo:
        GET /meuapp/extract-api/extract?job_id=TTBRASIL_20251120
    """

    # Captura o job_id
    job_id = request.args.get("job_id")

    # Se vier via POST JSON
    if not job_id:
        try:
            payload = request.get_json(silent=True) or {}
            job_id = payload.get("job_id")
        except Exception:
            job_id = None

    if not job_id:
        return jsonify({
            "ok": False,
            "erro": "Parâmetro 'job_id' ausente. Ex: /extract?job_id=TTBRASIL_20251120"
        }), 400

    try:
        # Executa o pipeline
        output_path = run_extract_pipeline(job_id)

        # Carrega o JSON consolidado para retornar contagem
        products_count = 0
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                products_count = data.get("products_count", 0)
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "job_id": job_id,
            "output_file": output_path,
            "products_count": products_count
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "erro": str(e),
            "job_id": job_id
        }), 500


# ============================================================
# 🔹 ROTA: /status (opcional, rápido)
# ============================================================
@extract_bp.route("/status", methods=["GET"])
def extract_status():
    """
    Apenas retorna mensagem simples para validar funcionamento do blueprint.
    """
    return jsonify({"ok": True, "status": "extract_api funcionando"})
