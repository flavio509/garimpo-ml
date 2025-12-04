"""
pipeline_extract_products.py

Pipeline responsável por:
- Ler JSONs de OCR por página (ocr_page_XX.json)
- Aplicar heurísticas híbridas (texto + posição) para extrair produtos
- Consolidar os produtos em um único JSON por job
- Servir como etapa intermediária para /extract e HTML de visualização

Este módulo NÃO depende de estado de chat.
Trabalha apenas com:
- job_id
- estrutura de diretórios em core_pipeline/data/<job_id>/
"""

import os
import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple

# Configuração básica de logging para uso em serviços e linha de comando
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )


# -----------------------------
# Convenções de diretório
# -----------------------------

DEFAULT_DATA_ROOT = "core_pipeline/data"


def get_job_paths(job_id: str, data_root: str = DEFAULT_DATA_ROOT) -> Dict[str, str]:
    """
    Retorna os caminhos relevantes para uma job.

    Estrutura esperada (consistente com SYSTEM_CONFIG/CONTEXT_BOOT):
    core_pipeline/data/<job_id>/
        uploads/
        outputs/
        pages/       (opcional)
        ocr/         (opcional)
    """
    base_dir = os.path.join(data_root, job_id)
    return {
        "base": base_dir,
        "uploads": os.path.join(base_dir, "uploads"),
        "outputs": os.path.join(base_dir, "outputs"),
        "pages": os.path.join(base_dir, "pages"),
        "ocr": os.path.join(base_dir, "ocr"),
    }


# -----------------------------
# Utilitários de leitura OCR
# -----------------------------

def find_ocr_json_files(job_paths: Dict[str, str]) -> List[str]:
    """
    Procura arquivos OCR JSON (ocr_page_XX.json) nas pastas mais prováveis:
    - outputs/
    - pages/
    - ocr/

    Retorna lista de caminhos absolutos, ordenada alfabeticamente.
    """
    candidates: List[str] = []
    possible_dirs = ["outputs", "pages", "ocr"]

    for key in possible_dirs:
        dir_path = job_paths.get(key)
        if not dir_path or not os.path.isdir(dir_path):
            continue

        for name in os.listdir(dir_path):
            if name.lower().startswith("ocr_page_") and name.lower().endswith(".json"):
                candidates.append(os.path.join(dir_path, name))

    candidates.sort()
    return candidates


def load_ocr_json(path: str) -> Optional[Dict[str, Any]]:
    """
    Carrega um único arquivo de OCR JSON de forma tolerante.
    Retorna dict ou None em caso de erro.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error("Falha ao carregar OCR JSON %s: %s", path, e)
        return None


# -----------------------------
# Heurísticas de extração
# -----------------------------

_PRICE_REGEX = re.compile(
    r"""
    (?<!\d)           # não precedido por dígito
    \d{1,5}           # 1–5 dígitos
    [,.]              # separador decimal
    \d{2}             # 2 casas decimais
    (?!\d)            # não seguido por dígito
    """,
    re.VERBOSE,
)


def extract_text_candidates(ocr_page: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrai candidatos de texto de uma página OCR, de forma genérica/tolerante.

    Tenta alguns padrões comuns:
    - ocr_page["blocks"]
    - ocr_page["lines"]
    - ocr_page["tokens"]

    Cada item retornado é um dict com:
    - text: str
    - bbox: Optional[Tuple[float, float, float, float]]
    """
    candidates: List[Dict[str, Any]] = []

    # Caso 1: estrutura por 'blocks'
    blocks = ocr_page.get("blocks") or ocr_page.get("Blocks") or []
    if isinstance(blocks, list):
        for b in blocks:
            text = b.get("text") or b.get("Text") or ""
            if not isinstance(text, str) or not text.strip():
                continue
            bbox = b.get("bbox") or b.get("bounding_box") or b.get("BoundingBox")
            candidates.append({
                "text": text.strip(),
                "bbox": bbox,
            })

    # Caso 2: estrutura por 'lines'
    lines = ocr_page.get("lines") or ocr_page.get("Lines") or []
    if isinstance(lines, list):
        for l in lines:
            text = l.get("text") or l.get("Text") or ""
            if not isinstance(text, str) or not text.strip():
                continue
            bbox = l.get("bbox") or l.get("bounding_box") or l.get("BoundingBox")
            candidates.append({
                "text": text.strip(),
                "bbox": bbox,
            })

    # Caso 3: tokens isolados (fallback)
    tokens = ocr_page.get("tokens") or ocr_page.get("Tokens") or []
    if isinstance(tokens, list):
        for t in tokens:
            text = t.get("text") or t.get("Text") or ""
            if not isinstance(text, str) or not text.strip():
                continue
            bbox = t.get("bbox") or t.get("bounding_box") or t.get("BoundingBox")
            candidates.append({
                "text": text.strip(),
                "bbox": bbox,
            })

    return candidates


def detect_price(text: str) -> Optional[str]:
    """
    Detecta um preço dentro de um texto usando regex simples.

    Retorna string do preço no formato encontrado ou None.
    """
    if not text:
        return None
    m = _PRICE_REGEX.search(text)
    if not m:
        return None
    return m.group(0)


def normalize_price(value: str) -> Optional[float]:
    """
    Normaliza uma string de preço para float (R$):
    - troca vírgula por ponto
    - valida se é numérico
    """
    if not value:
        return None
    try:
        cleaned = value.replace("R$", "").replace(" ", "").replace(",", ".")
        return float(cleaned)
    except Exception:
        return None


def build_product_from_candidate(
    candidate: Dict[str, Any],
    page_number: int,
) -> Optional[Dict[str, Any]]:
    """
    A partir de um candidato de texto (bloco/linha/token), tenta montar um produto.

    Heurística mínima:
    - deve conter um padrão de preço
    - descrição = texto completo (podendo ser refinado depois)
    - bbox = se existir no OCR
    """
    text = candidate.get("text") or ""
    if not text.strip():
        return None

    price_str = detect_price(text)
    if not price_str:
        return None

    price_value = normalize_price(price_str)
    bbox = candidate.get("bbox")

    product = {
        "description": text.strip(),
        "price_raw": price_str,
        "price": price_value,
        "page": page_number,
        "bbox": bbox,
    }
    return product


def extract_products_from_page(
    ocr_page: Dict[str, Any],
    page_number: int,
) -> List[Dict[str, Any]]:
    """
    Extrai produtos de um OCR JSON de página.

    Estratégia:
    - extrai candidatos de texto
    - para cada candidato, verifica se há padrão de preço
    - monta estrutura mínima de produto
    """
    products: List[Dict[str, Any]] = []
    candidates = extract_text_candidates(ocr_page)

    for cand in candidates:
        product = build_product_from_candidate(cand, page_number)
        if product is not None:
            products.append(product)

    return products


# -----------------------------
# Normalização de produtos
# -----------------------------

def normalize_product_fields(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aplica normalizações finais em um produto extraído.

    Aqui podem ser adicionadas:
    - limpeza adicional de descrição
    - padronização de campos
    - validações
    """
    description = product.get("description") or ""
    description = " ".join(description.split())

    price = product.get("price")
    price_raw = product.get("price_raw")

    normalized = {
        "description": description,
        "price": price,
        "price_raw": price_raw,
        "page": product.get("page"),
        "bbox": product.get("bbox"),
    }
    return normalized


def deduplicate_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicados simples com base em (description, price, page).
    """
    seen = set()
    result: List[Dict[str, Any]] = []

    for p in products:
        key = (p.get("description"), p.get("price"), p.get("page"))
        if key in seen:
            continue
        seen.add(key)
        result.append(p)

    return result


# -----------------------------
# Pipeline principal
# -----------------------------

def run(
    job_id: str,
    data_root: str = DEFAULT_DATA_ROOT,
    output_filename: str = "products_extracted.json",
) -> str:
    """
    Executa o pipeline de extração de produtos para uma job.

    Parâmetros:
        job_id: identificador da job (ex.: "TTBRASIL_20251120")
        data_root: raiz dos dados de pipeline (default: "core_pipeline/data")
        output_filename: nome do arquivo JSON a ser gerado em outputs/

    Retorna:
        Caminho absoluto do arquivo JSON gerado.
    """
    logger.info("Iniciando pipeline_extract_products para job_id=%s", job_id)

    job_paths = get_job_paths(job_id, data_root=data_root)
    base_dir = job_paths["base"]
    outputs_dir = job_paths["outputs"]

    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Diretório da job não encontrado: {base_dir}")

    if not os.path.isdir(outputs_dir):
        os.makedirs(outputs_dir, exist_ok=True)

    ocr_files = find_ocr_json_files(job_paths)
    if not ocr_files:
        logger.warning("Nenhum OCR JSON encontrado para job_id=%s", job_id)

    all_products: List[Dict[str, Any]] = []

    for idx, path in enumerate(ocr_files, start=1):
        page_number = idx  # mapeamento simples: ordem de arquivo -> número de página
        ocr_data = load_ocr_json(path)
        if ocr_data is None:
            continue

        page_products = extract_products_from_page(ocr_data, page_number)
        if page_products:
            logger.info(
                "Página %s - %d produtos extraídos do arquivo %s",
                page_number,
                len(page_products),
                os.path.basename(path),
            )
        all_products.extend(page_products)

    # Normalização e deduplicação
    normalized_products = [normalize_product_fields(p) for p in all_products]
    final_products = deduplicate_products(normalized_products)

    # Escrita do JSON consolidado
    output_path = os.path.join(outputs_dir, output_filename)
    result_payload = {
        "job_id": job_id,
        "products_count": len(final_products),
        "products": final_products,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, ensure_ascii=False, indent=2)

    logger.info(
        "Pipeline_extract_products concluído: %d produtos; saída: %s",
        len(final_products),
        output_path,
    )

    return output_path


# -----------------------------
# Entry point CLI
# -----------------------------

def _parse_args(argv: List[str]) -> Tuple[str, str]:
    """
    Parser mínimo de argumentos para linha de comando.

    Uso:
        python pipeline_extract_products.py <job_id> [data_root]

    Retorna:
        (job_id, data_root)
    """
    if len(argv) < 2:
        raise SystemExit(
            "Uso: python pipeline_extract_products.py <job_id> [data_root]\n"
            "Exemplo: python pipeline_extract_products.py TTBRASIL_20251120 core_pipeline/data"
        )

    job_id = argv[1]
    data_root = argv[2] if len(argv) >= 3 else DEFAULT_DATA_ROOT
    return job_id, data_root


if __name__ == "__main__":
    import sys

    job_id_arg, data_root_arg = _parse_args(sys.argv)
    out = run(job_id_arg, data_root=data_root_arg)
    print(out)
