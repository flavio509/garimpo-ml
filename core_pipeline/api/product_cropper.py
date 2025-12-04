import os
import traceback
import cv2


def _safe_crop(img, x1, y1, x2, y2):
    """
    Recorte seguro garantindo que o bbox esteja dentro dos limites da imagem.
    """
    h, w = img.shape[:2]
    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w - 1))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h - 1))

    if x2 <= x1 or y2 <= y1:
        return None

    return img[y1:y2, x1:x2]


def crop_product_from_page(
    image_path,
    bbox,
    output_path,
    margin_ratio=0.03
):
    """
    Recorta um produto da página usando seu bounding box.

    Args:
        image_path (str): caminho da imagem completa da página.
        bbox (list): [x1, y1, x2, y2] do produto.
        output_path (str): caminho onde o recorte será salvo.
        margin_ratio (float): margem percentual para expandir o recorte.

    Returns:
        dict: status, bbox_final, output_path, erro.
    """

    result = {
        "status": "error",
        "image_path": image_path,
        "bbox_input": bbox,
        "bbox_final": None,
        "output_path": output_path,
        "error": None
    }

    try:
        if not os.path.exists(image_path):
            result["error"] = f"Imagem da página não encontrada: {image_path}"
            return result

        img = cv2.imread(image_path)
        if img is None:
            result["error"] = f"Falha ao carregar imagem: {image_path}"
            return result

        h, w = img.shape[:2]

        if not bbox or len(bbox) != 4:
            result["error"] = f"BBox inválido: {bbox}"
            return result

        x1, y1, x2, y2 = bbox

        # Expansão de margem proporcional ao tamanho da página
        mx = int(w * margin_ratio)
        my = int(h * margin_ratio)
        x1 -= mx
        x2 += mx
        y1 -= my
        y2 += my

        # Recorte seguro
        crop = _safe_crop(img, x1, y1, x2, y2)
        if crop is None:
            result["error"] = "BBox inválido após aplicação de margem."
            return result

        # Garante diretório de saída
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        cv2.imwrite(output_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])

        result["status"] = "success"
        result["bbox_final"] = [x1, y1, x2, y2]
        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result


def crop_products_from_list(
    image_path,
    products,
    output_dir,
    margin_ratio=0.03
):
    """
    Efetua o crop de vários produtos de uma mesma página.

    Args:
        image_path (str): caminho da página original.
        products (list): lista de dicts contendo:
          {
            "code": ...,
            "description": ...,
            "price_value": ...,
            "bbox": [x1, y1, x2, y2],
            "block_id": ...
          }
        output_dir (str): pasta onde os recortes serão salvos.
        margin_ratio (float): margem percentual.

    Returns:
        dict: status, items (detalhes por produto), erro.
    """

    result = {
        "status": "error",
        "image_path": image_path,
        "output_dir": output_dir,
        "items": [],
        "error": None
    }

    try:
        if not os.path.exists(image_path):
            result["error"] = f"Imagem da página não encontrada: {image_path}"
            return result

        img = cv2.imread(image_path)
        if img is None:
            result["error"] = f"Falha ao carregar imagem: {image_path}"
            return result

        os.makedirs(output_dir, exist_ok=True)

        h, w = img.shape[:2]

        for idx, prod in enumerate(products):
            bbox = prod.get("bbox")
            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox

            # Margem proporcional
            mx = int(w * margin_ratio)
            my = int(h * margin_ratio)
            x1 -= mx
            x2 += mx
            y1 -= my
            y2 += my

            crop = _safe_crop(img, x1, y1, x2, y2)
            if crop is None:
                continue

            filename = f"product_{idx:04d}.jpg"
            out_path = os.path.join(output_dir, filename)

            cv2.imwrite(out_path, crop, [cv2.IMWRITE_JPEG_QUALITY, 95])

            result["items"].append({
                "product_index": idx,
                "output_path": out_path,
                "bbox_final": [x1, y1, x2, y2]
            })

        result["status"] = "success"
        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result
