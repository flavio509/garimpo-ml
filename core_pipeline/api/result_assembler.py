import os
import json
import traceback
from typing import List, Dict, Any, Optional


def _normalize_code(code: Optional[str]) -> Optional[str]:
    """
    Normaliza código de produto (ex: CT12345 → CT12345 sem espaços, upper).
    """
    if not code:
        return None
    if not isinstance(code, str):
        return None
    code = code.strip().upper()
    code = code.replace(" ", "")
    return code or None


def _normalize_description(description: Optional[str]) -> Optional[str]:
    """
    Normaliza descrição removendo espaços duplicados e trim.
    """
    if not description:
        return None
    if not isinstance(description, str):
        return None
    desc = " ".join(description.split())
    return desc or None


def _build_product_entry(
    product: Dict[str, Any],
    crop_info: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Monta o registro final de produto combinando:
      - campos sem imagem (detector)
      - dados de crop (se existirem)
    """
    code = _normalize_code(product.get("code"))
    desc = _normalize_description(product.get("description"))
    price_value = product.get("price_value")
    price_text = product.get("price_text")

    page_index = product.get("page_index")
    column_index = product.get("column_index")
    block_id = product.get("block_id")
    bbox = product.get("bbox")

    image_path = None
    bbox_final = None
    if crop_info is not None:
        image_path = crop_info.get("output_path")
        bbox_final = crop_info.get("bbox_final") or bbox

    entry = {
        "code": code,
        "description": desc,
        "price_value": price_value,
        "price_text": price_text,
        "image_path": image_path,
        "page_index": page_index,
        "column_index": column_index,
        "block_id": block_id,
        "bbox": bbox_final or bbox,
    }

    return entry


def assemble_page_products(
    products: List[Dict[str, Any]],
    crop_result: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Consolida produtos de UMA página, combinando:
      - lista de produtos detectados (product_detector)
      - resultado do crop (product_cropper.crop_products_from_list)

    Contratos esperados:

      products: lista no formato retornado por product_detector.detect_products_from_blocks:
        [
          {
            "code": ...,
            "description": ...,
            "price_text": ...,
            "price_value": ...,
            "page_index": ...,
            "column_index": ...,
            "block_id": ...,
            "bbox": [x1, y1, x2, y2],
          },
          ...
        ]

      crop_result: dict no formato retornado por product_cropper.crop_products_from_list:
        {
          "status": "success" | "error",
          "image_path": "...",
          "output_dir": "...",
          "items": [
            {
              "product_index": int,
              "output_path": "...",
              "bbox_final": [x1, y1, x2, y2]
            },
            ...
          ],
          "error": ...
        }

    Associação produto ↔ crop é feita por "product_index" usando a mesma ordem
    passada ao cropper (enumerate(products)).
    """
    if crop_result is not None:
        items = crop_result.get("items", [])
        crop_map = {
            int(item.get("product_index")): item
            for item in items
            if "product_index" in item
        }
    else:
        crop_map = {}

    final_products: List[Dict[str, Any]] = []
    for idx, prod in enumerate(products):
        crop_info = crop_map.get(idx)
        entry = _build_product_entry(prod, crop_info)
        final_products.append(entry)

    return final_products


def assemble_catalog(
    pages_data: List[Dict[str, Any]],
    output_json_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Consolida TODOS os produtos de TODAS as páginas em uma única lista.

    pages_data deve ser uma lista de dicts, um por página, com estrutura típica:

      {
        "page_index": int (opcional),
        "detector_result": {
            "status": "success",
            "products": [...]
        },
        "crop_result": {
            "status": "success",
            "items": [...]
        }
      }

    Onde:
      - detector_result["products"] é a lista de produtos desta página
      - crop_result é o dict retornado por crop_products_from_list

    Saída:
      {
        "status": "success" | "error",
        "products": [ ... lista consolidada ... ],
        "error": str | None
      }

    Se output_json_path for fornecido, salva o JSON final:
      [
        {... produto 1 ...},
        {... produto 2 ...},
        ...
      ]
    """
    result: Dict[str, Any] = {
        "status": "error",
        "products": [],
        "error": None,
    }

    try:
        all_products: List[Dict[str, Any]] = []

        for page_info in pages_data:
            page_index = page_info.get("page_index")

            detector = page_info.get("detector_result") or {}
            crop_res = page_info.get("crop_result")

            products_page = detector.get("products") or []
            # Se page_index não veio dentro de cada produto, garante preenchimento
            for p in products_page:
                if p.get("page_index") is None and page_index is not None:
                    p["page_index"] = page_index

            assembled_page = assemble_page_products(
                products=products_page,
                crop_result=crop_res,
            )

            all_products.extend(assembled_page)

        result["status"] = "success"
        result["products"] = all_products

        if output_json_path:
            out_dir = os.path.dirname(output_json_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)

        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result
