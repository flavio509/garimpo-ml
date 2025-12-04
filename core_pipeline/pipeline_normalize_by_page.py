import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/home/ubuntu/garimpo-ml")
OUT_BASE = BASE_DIR / "core_pipeline" / "outputs"

def _clean(raw: str) -> str:
    if not raw:
        return ""
    return (raw.replace("O","0").replace("o","0")
                .replace("S","5").replace("s","5")
                .replace("I","1").replace("l","1")
                .replace("E","8").replace("B","8"))

def norm_code(txt: str) -> str:
    if not txt: return ""
    m = re.search(r"\bCT\d{3,6}\b", txt, flags=re.I)
    return m.group(0).upper() if m else ""

def norm_price(txt: str) -> str:
    if not txt: return ""
    clean = _clean(txt)
    m = re.search(r"R\$ ?([\d\.,]+)", clean, flags=re.I)
    if not m: return ""
    num = m.group(1).replace(".", "").replace(",", ".")
    try: value = float(num)
    except: return ""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def norm_title(txt: str) -> str:
    if not txt: return ""
    t = re.sub(r"\bCT\d{3,6}\b", "", txt, flags=re.I)
    t = re.sub(r"R\$ ?[\d\.,]+", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()

def normalize_upload(job_id: str):
    out_dir = OUT_BASE / job_id
    if not out_dir.exists():
        print(f"❌ {out_dir} não encontrado")
        return

    files = sorted(out_dir.glob("page_*_ocr.json"),
                   key=lambda p: int(re.findall(r"\d+", p.stem)[0]))

    for ocr_path in files:
        pg = int(re.findall(r"\d+", ocr_path.stem)[0])
        data = json.loads(ocr_path.read_text())

        norm = []
        for blk in data:
            raw = blk.get("original","")
            codigo = blk.get("codigo") or norm_code(raw)
            preco  = blk.get("preco")  or norm_price(raw)
            titulo = blk.get("titulo") or norm_title(raw)

            img = blk.get("imagem") or ""
            if not img and codigo:
                img = f"/crops/page_{pg:02d}_{codigo}.jpg"

            norm.append({
                "page": pg,
                "codigo": codigo,
                "titulo": titulo,
                "preco": preco,
                "imagem": img,
                "fonte": "ocr_normalized",
                "original": raw
            })

        out_norm = out_dir / f"normalized_page_{pg:02d}.json"
        out_norm.write_text(json.dumps(norm, ensure_ascii=False, indent=2))

        print(f"✅ Página {pg}: {len(norm)} normalizados")

    print("🎯 Normalização concluída.")

if __name__ == "__main__":
    import sys
    normalize_upload(sys.argv[1])