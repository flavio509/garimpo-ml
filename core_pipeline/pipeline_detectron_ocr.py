import pytesseract, json
import cv2
from pathlib import Path

IN_DIR = Path("data/pages")
OUT_DIR = Path("core_pipeline/outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("🚀 Executando OCR em todas as páginas...")
all_blocks = []

for img_file in sorted(IN_DIR.glob("page_*.jpg")):
    img = cv2.imread(str(img_file))
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang="por")
    blocks = []
    for i in range(len(data["text"])):
        txt = data["text"][i].strip()
        if not txt:
            continue
        blocks.append({"text": txt, "page": img_file.stem, "conf": data["conf"][i]})
    out_json = OUT_DIR / f"{img_file.stem}_ocr.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)
    all_blocks.extend(blocks)
    print(f"✅ {img_file.name}: {len(blocks)} blocos extraídos → {out_json.name}")

print(f"🎯 OCR concluído para {len(list(IN_DIR.glob('page_*.jpg')))} páginas.")
