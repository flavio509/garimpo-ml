import os
import re
import json
from pathlib import Path
from collections import defaultdict
import cv2
import pytesseract
from pytesseract import Output

BASE_DIR = Path("/home/ubuntu/garimpo-ml")
# CORRETO: onde realmente estão as páginas hoje
PAGES_BASE = BASE_DIR / "core_pipeline" / "data"
OUTPUTS_BASE = BASE_DIR / "core_pipeline" / "outputs"

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def norm_code(text: str) -> str:
    m = re.search(r"\bCT\d{3,6}\b", text or "", flags=re.I)
    return m.group(0).upper() if m else ""

def norm_price(text: str) -> str:
    m = re.search(r"R\$ ?([\d\.,]+)", text or "", flags=re.I)
    return f"R$ {m.group(1)}" if m else ""

def norm_title(text: str) -> str:
    t = re.sub(r"\bCT\d{3,6}\b|R\$ ?[\d\.,]+", "", text or "", flags=re.I)
    return re.sub(r"\s+", " ", t.strip())

def _sorted_pages(pages_dir: Path):
    pages = list(pages_dir.glob("*.jpg"))
    pages.sort(key=lambda p: int(re.findall(r"\d+", p.stem)[0]))
    return pages

def process_pages(job_id: str):
    pages_dir = PAGES_BASE / job_id / "outputs" / "pages_jpg"
    out_dir = OUTPUTS_BASE / job_id
    ensure_dir(out_dir)

    if not pages_dir.exists():
        print(f"❌ Diretório de páginas não encontrado: {pages_dir}")
        return

    imgs = _sorted_pages(pages_dir)
    print(f"🧠 Encontradas {len(imgs)} páginas em: {pages_dir}")

    for img_path in imgs:
        page_num = int(re.findall(r"\d+", img_path.stem)[0])

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"⚠️ Falha ao abrir {img_path}")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31, 2
        )

        ocr = pytesseract.image_to_data(
            thresh,
            lang="por",
            output_type=Output.DICT
        )

        line_map = defaultdict(list)

        n = len(ocr["text"])
        for i in range(n):
            txt = (ocr["text"][i] or "").strip()
            if not txt:
                continue
            try:
                conf = float(ocr["conf"][i])
            except:
                conf = 0
            if conf < 0:
                continue

            y = ocr["top"][i]
            key = y // 30
            line_map[key].append(txt)

        produtos = []
        for _, words in sorted(line_map.items()):
            joined = " ".join(words)
            codigo = norm_code(joined)
            preco = norm_price(joined)
            titulo = norm_title(joined)

            if codigo or preco or titulo:
                produtos.append({
                    "page": page_num,
                    "codigo": codigo,
                    "titulo": titulo,
                    "preco": preco,
                    "original": joined,
                    "fonte": "ocr_auto"
                })

        out_json = out_dir / f"page_{page_num:02d}_ocr.json"
        out_json.write_text(json.dumps(produtos, ensure_ascii=False, indent=2))

        print(f"✅ Página {page_num}: {len(produtos)} blocos → {out_json}")

    print("🎯 OCR concluído.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python3 ocr_page_processor.py <JOB_ID>")
        raise SystemExit(1)
    process_pages(sys.argv[1])