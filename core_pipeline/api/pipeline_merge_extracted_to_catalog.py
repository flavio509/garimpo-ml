"""
pipeline_merge_extracted_to_catalog.py

Responsável por:
- Ler o resultado da extração de produtos (products_extracted.json)
- Converter/normalizar para o formato usado pelo catálogo final
- Gravar em core_pipeline/outputs/merged_output.json

Integração:
- Entrada: core_pipeline/data/<JOB_ID>/outputs/products_extracted.json
- Saída:   core_pipeline/outputs/merged_output.json

Regra de código (campo 'codigo'):
- Se já vier no JSON de entrada -> preservar.
- Se NÃO existir -> deixar em branco (""), sem gerar código artificial.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

# Configuração básica de logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

# Raiz do projeto (compatível com paths já usados)
BASE_DIR = "/home/ubuntu/garimpo-ml"
DATA_ROOT = os.path.join(BASE_DIR, "core_pipeline", "data")
OUTPUTS_DIR = os.path.join(BASE_DIR, "core_pipeline", "outputs")
MERGED_FILE = os.path.join(OUTPUTS_DIR, "merged_output.json")


def load_extracted_products(job_id: str) -> Dict[str, Any]:
    """
    Carrega o products_extracted.json de uma job específica.

    Estrutura esperada (gerada pelo pipeline_extract_products):
    {
        "job_id": "<job_id>",
        "products_count": <int>,
        "products": [ { ... } ]
    }
    """
    job_base = os.path.join(DATA_ROOT, job_id)
    outputs_dir = os.path.join(job_base, "outputs")
    json_path = os.path.join(outputs_dir, "products_extracted.json")

    if not os.path.isdir(outputs_dir):
        raise FileNotFoundError(f"Diretório outputs da job não encontrado: {outputs_dir}")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Arquivo products_extracted.json não encontrado: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Estrutura de products_extracted.json inválida (esperado dict).")

    return data


def normalize_product_for_catalog(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza um produto do formato da extração para o formato do catálogo final.

    Entrada típica (products_extracted.json):
        {
            "description": str,
            "price": float | null,
            "price_raw": str,
            "page": int,
            "bbox": ...
            [opcional] "codigo": str
        }

    Saída esperada para o catálogo (merged_output.json):
        {
            "codigo": str,
            "descricao": str,
            "preco": float | null,
            "preco_raw": str,
            "page": int,
            "bbox": ...
        }

    Regra:
    - codigo: se existir em raw -> usar; senão -> ""
    """
    codigo = raw.get("codigo")
    if codigo is None:
        codigo = ""

    descricao = raw.get("description") or ""
    if not isinstance(descricao, str):
        descricao = str(descricao)

    preco = raw.get("price")
    # Se vier string, tenta converter
    if isinstance(preco, str):
        try:
            preco = float(preco.replace(",", "."))
        except Exception:
            preco = None

    preco_raw = raw.get("price_raw") or ""
    page = raw.get("page")
    bbox = raw.get("bbox")

    return {
        "codigo": codigo,
        "descricao": descricao,
        "preco": preco,
        "preco_raw": preco_raw,
        "page": page,
        "bbox": bbox,
    }


def merge_extracted_to_catalog(job_id: str) -> str:
    """
    Função principal do pipeline.

    - Lê products_extracted.json da job
    - Converte/normaliza produtos
    - Grava lista final em MERGED_FILE (core_pipeline/outputs/merged_output.json)

    Retorna:
        Caminho do arquivo merged_output.json gerado.
    """
    logger.info("Iniciando merge de extração para catálogo. job_id=%s", job_id)

    data = load_extracted_products(job_id)
    products_raw = data.get("products") or []

    if not isinstance(products_raw, list):
        raise ValueError("Campo 'products' em products_extracted.json deve ser uma lista.")

    normalized: List[Dict[str, Any]] = []
    for p in products_raw:
        if not isinstance(p, dict):
            continue
        normalized.append(normalize_product_for_catalog(p))

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    with open(MERGED_FILE, "w", encoding="utf-8") as f:
        # O catalog_api.py espera uma LISTA de produtos, não um dict wrapper.
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    logger.info(
        "Merge concluído. %d produtos salvos em %s",
        len(normalized),
        MERGED_FILE,
    )
    return MERGED_FILE


# ------------------------------------------------------
# Entry point de linha de comando
# ------------------------------------------------------

def _parse_args(argv: List[str]) -> str:
    """
    Parser mínimo de argumentos para CLI.

    Uso:
        python pipeline_merge_extracted_to_catalog.py <JOB_ID>

    Exemplo:
        python pipeline_merge_extracted_to_catalog.py TTBRASIL_20251120
    """
    if len(argv) < 2:
        raise SystemExit(
            "Uso: python pipeline_merge_extracted_to_catalog.py <JOB_ID>\n"
            "Exemplo: python pipeline_merge_extracted_to_catalog.py TTBRASIL_20251120"
        )
    return argv[1]


if __name__ == "__main__":
    import sys

    job_id_arg = _parse_args(sys.argv)
    out_path = merge_extracted_to_catalog(job_id_arg)
    print(out_path)
