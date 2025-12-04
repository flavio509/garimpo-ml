import os
import json
import re
import traceback
from typing import List, Dict, Any, Optional


# Regex para códigos tipo CTxxxxx (flexível, mas focado no padrão validado)
CODE_REGEX = re.compile(r"\bCT\s*\d{3,}\b", re.IGNORECASE)

# Regex para preços em formato BR (12,34 ou 1.234,56) e fallback simples
PRICE_REGEX = re.compile(
    r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2})"
)


def _normalize_price_to_float(price_str: str) -> Optional[float]:
    """
    Converte string de preço em float (formato interno).
    Suporta:
        - 1.234,56
        - 12,34
        - 12.34

    Retorna float ou None se não conseguir converter.
    """
    if not price_str:
        return None

    s = price_str.strip()

    # Remove símbolo de moeda
    s = re.sub(r"[Rr]\$\s*", "", s)

    # Caso clássico BR: pontos de milhar + vírgula como decimal
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    # Caso apenas ponto, já está ok

    try:
        return float(s)
    except ValueError:
        return None


def _extract_code_from_text(text: str) -> Optional[str]:
    """
    Busca o primeiro código CTxxxxx no texto.
    """
    if not text:
        return None
    m = CODE_REGEX.search(text)
    if not m:
        return None
    # Normaliza: CT + números, removendo espaços internos
    raw = m.group(0)
    normalized = re.sub(r"\s+", "", raw.upper())
    return normalized


def _extract_price_from_text(text: str) -> Dict[str, Any]:
    """
    Busca preços no texto e retorna o maior valor encontrado como preço do produto.

    Retorno:
        {
            "price_text": str | None,
            "price_value": float | None
        }
    """
    best_price_text = None
    best_price_value = None

    if not text:
        return {"price_text": None, "price_value": None}

    for m in PRICE_REGEX.finditer(text):
        candidate = m.group(1)
        value = _normalize_price_to_float(candidate)
        if value is None:
            continue
        if best_price_value is None or value > best_price_value:
            best_price_value = value
            best_price_text = candidate

    return {"price_text": best_price_text, "price_value": best_price_value}


def _compute_token_center(token: Dict[str, Any]) -> Optional[tuple]:
    """
    Retorna o centro (cx, cy) do token com base em bbox [x1, y1, x2, y2].

    Se bbox ausente ou inválido, retorna None.
    """
    bbox = token.get("bbox") or token.get("box") or token.get("rect")
    if not bbox or len(bbox) != 4:
        return None
    x1, y1, x2, y2 = bbox
    try:
        cx = (float(x1) + float(x2)) / 2.0
        cy = (float(y1) + float(y2)) / 2.0
        return cx, cy
    except Exception:
        return None


def _assign_tokens_to_blocks(
    tokens: List[Dict[str, Any]],
    blocks: List[Dict[str, Any]],
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Associa tokens a blocos (por id), usando o centro do token
    e os bboxes dos blocos.

    blocks: lista com elementos contendo:
        {
            "id": int,
            "column_index": int,
            "bbox": [x1, y1, x2, y2]
        }

    Retorna:
        dict: {block_id: [tokens...]}
    """
    block_map: Dict[int, List[Dict[str, Any]]] = {b["id"]: [] for b in blocks}

    for token in tokens:
        center = _compute_token_center(token)
        if center is None:
            continue
        cx, cy = center

        for b in blocks:
            bx1, by1, bx2, by2 = b["bbox"]
            if bx1 <= cx <= bx2 and by1 <= cy <= by2:
                block_map[b["id"]].append(token)
                break

    return block_map


def _sort_tokens_reading_order(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ordena tokens em ordem de leitura aproximada (top->bottom, left->right).
    """
    def _key(t):
        bbox = t.get("bbox") or t.get("box") or t.get("rect") or [0, 0, 0, 0]
        if len(bbox) != 4:
            return (0, 0)
        x1, y1, _, _ = bbox
        return (y1, x1)

    return sorted(tokens, key=_key)


def _merge_tokens_text(tokens: List[Dict[str, Any]]) -> str:
    """
    Junta os textos dos tokens em uma string única.
    """
    parts = []
    for t in tokens:
        txt = t.get("text") or t.get("txt") or ""
        if not isinstance(txt, str):
            continue
        txt = txt.strip()
        if txt:
            parts.append(txt)
    return " ".join(parts)


def detect_products_from_blocks(
    ocr_tokens: List[Dict[str, Any]],
    blocks: List[Dict[str, Any]],
    page_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Núcleo de detecção de produtos a partir de:
        - tokens OCR (com bbox por token)
        - blocos segmentados (coluna + linha)

    Entrada:
        ocr_tokens: lista de tokens (dict), idealmente contendo:
            {
                "text": str,
                "bbox": [x1, y1, x2, y2],
                ...
            }
        blocks: lista de blocos:
            {
                "id": int,
                "column_index": int,
                "bbox": [x1, y1, x2, y2],
            }
        page_index: índice da página (0-based ou 1-based, apenas metadado).

    Saída:
        {
            "status": "success" | "error",
            "page_index": page_index,
            "products": [
                {
                    "code": str | None,
                    "description": str | None,
                    "price_text": str | None,
                    "price_value": float | None,
                    "page_index": int | None,
                    "column_index": int,
                    "block_id": int,
                    "bbox": [x1, y1, x2, y2],
                },
                ...
            ],
            "error": str | None
        }
    """
    result: Dict[str, Any] = {
        "status": "error",
        "page_index": page_index,
        "products": [],
        "error": None,
    }

    try:
        if not isinstance(ocr_tokens, list):
            result["error"] = "ocr_tokens deve ser uma lista."
            return result
        if not isinstance(blocks, list):
            result["error"] = "blocks deve ser uma lista."
            return result

        tokens_by_block = _assign_tokens_to_blocks(ocr_tokens, blocks)

        products = []

        for block in blocks:
            block_id = block.get("id")
            column_index = block.get("column_index", 0)
            bbox = block.get("bbox") or [0, 0, 0, 0]

            block_tokens = tokens_by_block.get(block_id, [])
            if not block_tokens:
                # bloco sem texto, ignorar
                continue

            block_tokens_sorted = _sort_tokens_reading_order(block_tokens)
            block_text = _merge_tokens_text(block_tokens_sorted)

            if not block_text.strip():
                continue

            # Extrair código
            code = _extract_code_from_text(block_text)

            # Extrair preço
            price_info = _extract_price_from_text(block_text)
            price_text = price_info["price_text"]
            price_value = price_info["price_value"]

            # Descrição = texto do bloco removendo código e preço (quando existir)
            description = block_text
            if code:
                description = description.replace(code, " ")
            if price_text:
                description = description.replace(price_text, " ")

            description = re.sub(r"\s+", " ", description).strip()
            if not description:
                description = None

            # Critério mínimo: precisa ter pelo menos um dos 3 (código, preço ou descrição)
            if not code and price_value is None and not description:
                continue

            product = {
                "code": code,
                "description": description,
                "price_text": price_text,
                "price_value": price_value,
                "page_index": page_index,
                "column_index": column_index,
                "block_id": block_id,
                "bbox": bbox,
            }
            products.append(product)

        result["status"] = "success"
        result["products"] = products
        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result


def detect_products_from_files(
    ocr_json_path: str,
    blocks_json_path: str,
    output_json_path: Optional[str] = None,
    page_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Versão conveniente que lê os dados de:
        - ocr_json_path: arquivo no formato produzido por ocr_page_processor.py
            {
                "image": "page_01.jpg",
                "tokens": [...]
            }
        - blocks_json_path: arquivo no formato produzido por line_segmenter.py
            {
                "image": "page_01.jpg",
                "width": ...,
                "height": ...,
                "columns": [...],
                "blocks": [...]
            }

    Se output_json_path for informado, salva o JSON de produtos.

    Retorna o mesmo dict de detect_products_from_blocks, com possível persistência em disco.
    """
    result: Dict[str, Any] = {
        "status": "error",
        "page_index": page_index,
        "products": [],
        "error": None,
    }

    try:
        if not os.path.exists(ocr_json_path):
            result["error"] = f"OCR JSON não encontrado: {ocr_json_path}"
            return result
        if not os.path.exists(blocks_json_path):
            result["error"] = f"Blocks JSON não encontrado: {blocks_json_path}"
            return result

        with open(ocr_json_path, "r", encoding="utf-8") as f:
            ocr_data = json.load(f)

        with open(blocks_json_path, "r", encoding="utf-8") as f:
            blocks_data = json.load(f)

        ocr_tokens = ocr_data.get("tokens", [])
        blocks = blocks_data.get("blocks", [])

        core_result = detect_products_from_blocks(
            ocr_tokens=ocr_tokens,
            blocks=blocks,
            page_index=page_index,
        )

        # Se solicitado, persistir
        if output_json_path is not None:
            out_dir = os.path.dirname(output_json_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(core_result, f, ensure_ascii=False, indent=2)

        return core_result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result
