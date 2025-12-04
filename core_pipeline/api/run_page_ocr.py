import sys
import os
sys.path.append("/home/ubuntu/garimpo-ml")

# ================================================
#  Garimpo ML – Executa OCR por página (fix2)
# ================================================

import os
import argparse
import cv2
from core_pipeline.calibra_p10.utils_calibra import find_boxes_multi
from core_pipeline.api.ocr_extract import extract_ocr
from PIL import Image

BASE_DIR = "/home/ubuntu/garimpo-ml"
PAGES_DIR = os.path.join(BASE_DIR, "data", "pages")
RECORTES_DIR = os.path.join(BASE_DIR, "core_pipeline", "outputs", "recortes")

os.makedirs(RECORTES_DIR, exist_ok=True)


def recortar_caixas(page_number):
    """Localiza caixas e salva recortes individuais."""
    img_path = os.path.join(PAGES_DIR, f"page_{page_number:02d}.jpg")
    img = Image.open(img_path)
    img_cv = cv2.imread(img_path)

    boxes = find_boxes_multi(img_cv)
    saved_paths = []

    for i, (x1, y1, x2, y2, conf) in enumerate(boxes):
        crop = img.crop((x1, y1, x2, y2))
        filename = f"page{page_number:02d}_box{i:03d}.jpg"
        out_path = os.path.join(RECORTES_DIR, filename)
        crop.save(out_path)
        saved_paths.append(out_path)

    return saved_paths


def processar_pagina(page_number):
    """Faz o recorte das caixas e executa OCR em cada uma."""
    recortes = recortar_caixas(page_number)
    resultados = []

    for r in recortes:
        resultado = extract_ocr(r, page_number)
        resultados.append(resultado)

    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()

    resultados = processar_pagina(args.page)
    print(f"OCR finalizado – {len(resultados)} caixas processadas")
