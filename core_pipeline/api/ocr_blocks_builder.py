"""
Garimpo ML – OCR Blocks Builder (v2025-11-12, fix v2)
-----------------------------------------------------
Executa OCR em cada página (page_XX.jpg) com coordenadas (bbox),
gerando core_pipeline/outputs/ocr_page_XX.json.
Compatível com qualquer versão de pytesseract (conf como str/int/float).
"""

import os, json, pytesseract
from pathlib import Path
from PIL import Image
from datetime import datetime

# ============================================================
# 🔹 Caminhos
# ============================================================
BASE_DIR = Path("/home/ubuntu/garimpo-ml")
DATA_DIR = BASE_DIR / "core_pipeline" / "data" / "TTBRASIL_20251112" / "outputs"
OUT_DIR = BASE_DIR / "core_pipeline" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 🔹 Função principal
# ============================================================
def processar_pagina(num: int):
    """
    Executa pytesseract.image_to_data e gera JSON de blocos OCR.
    """
    img_path = DATA_DIR / f"page_{num:02d}.jpg"
    if not img_path.exists():
        print(f"⚠️  Imagem não encontrada: {img_path}")
        return

    print(f"📄 Página {num:02d} → executando OCR (com coordenadas)...")

    img = Image.open(img_path)
    data = pytesseract.image_to_data(img, lang="por+eng", output_type=pytesseract.Output.DICT)

    blocks = []
    for i in range(len(data["text"])):
        texto = (str(data["text"][i]) or "").strip()
        if not texto:
            continue

        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]

        # 🩹 Compatibilidade de tipos para "conf"
        conf_raw = data.get("conf", [0])[i]
        try:
            conf = int(float(conf_raw))
        except Exception:
            conf = 0

        blocks.append({
            "text": texto,
            "x": int(x), "y": int(y), "w": int(w), "h": int(h),
            "conf": conf,
            "page": num
        })

    out_path = OUT_DIR / f"ocr_page_{num:02d}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "page": num,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "num_blocks": len(blocks),
            "blocks": blocks
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Página {num:02d} concluída → {out_path} ({len(blocks)} blocos)")

# ============================================================
# 🔹 Execução principal
# ============================================================
def main():
    print("🚀 Iniciando reconstrução OCR com coordenadas (Passo A v2)")
    paginas = sorted([int(p.stem.split("_")[1]) for p in DATA_DIR.glob("page_*.jpg")])
    for num in paginas:
        processar_pagina(num)
    print("🏁 OCR Blocks Builder finalizado com sucesso.")

if __name__ == "__main__":
    main()
