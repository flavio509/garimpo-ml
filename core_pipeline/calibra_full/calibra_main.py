"""
Garimpo ML - Calibração Completa de OCR Visual
Expande a calibração inicial (p10) para todas as páginas do PDF (11–33).
Usa OpenCV + Tesseract (sem Detectron2).
Gera arquivos ocr_page_##.json com bounding boxes e texto reconhecido.
"""

import os
import cv2
import pytesseract
import json
from datetime import datetime

BASE_DIR = "/home/ubuntu/garimpo-ml"
PAGES_DIR = os.path.join(BASE_DIR, "data", "pages")
OUTPUT_DIR = os.path.join(BASE_DIR, "core_pipeline", "outputs", "ocr_full")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_PATH = os.path.join(BASE_DIR, "logs", "calibra_full.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def process_page(page_num):
    filename = f"page_{page_num:02}.jpg"
    img_path = os.path.join(PAGES_DIR, filename)
    if not os.path.exists(img_path):
        log(f"[WARN] Arquivo não encontrado: {img_path}")
        return None

    log(f"[INFO] Processando {filename}")
    image = cv2.imread(img_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    custom_oem_psm_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT, config=custom_oem_psm_config)

    ocr_results = []
    for i in range(len(data["text"])):
        text = str(data["text"][i]).strip()
        if text:
            conf_raw = data["conf"][i]
            try:
                conf_val = int(conf_raw)
            except (ValueError, TypeError):
                conf_val = -1

            entry = {
                "text": text,
                "left": int(data["left"][i]),
                "top": int(data["top"][i]),
                "width": int(data["width"][i]),
                "height": int(data["height"][i]),
                "conf": conf_val
            }
            ocr_results.append(entry)

    out_file = os.path.join(OUTPUT_DIR, f"ocr_page_{page_num:02}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ocr_results, f, ensure_ascii=False, indent=2)
    log(f"[OK] Página {page_num:02} processada → {out_file}")

def main():
    log("==== INÍCIO calibra_full ====")
    for page_num in range(11, 34):
        process_page(page_num)
    log("==== FIM calibra_full ====")

if __name__ == "__main__":
    main()
