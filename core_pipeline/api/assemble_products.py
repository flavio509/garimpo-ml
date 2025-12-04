"""
Garimpo ML – Assemble Products (v2025-11-12, modo âncora por código)
--------------------------------------------------------------------
Lê ocr_page_XX.json, identifica blocos com padrão de CÓDIGO (âncora),
coleta somente os blocos na janela ao redor (título acima, preço perto),
gera crops e escreve products_page_XX.json.

Saída:
- core_pipeline/outputs/products_page_XX.json
- core_pipeline/outputs/crops/page_XX_<CODIGO|fallback>.jpg
"""

import os, re, json
from pathlib import Path
from datetime import datetime
from PIL import Image

# =========================
# Caminhos
# =========================
BASE_DIR  = Path("/home/ubuntu/garimpo-ml")
DATA_DIR  = BASE_DIR / "core_pipeline" / "data" / "TTBRASIL_20251112" / "outputs"
OUT_DIR   = BASE_DIR / "core_pipeline" / "outputs"
CROPS_DIR = OUT_DIR / "crops"
CROPS_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# Parâmetros (afináveis)
# =========================
CONF_MIN      = 45        # confiança mínima do bloco
MIN_TEXT_LEN  = 2         # ignora tokens 1-char
MAX_SYM_RATIO = 0.6       # ignora tokens muito simbólicos
DELTA_X_LEFT  = 220       # janela lateral à esquerda do CÓDIGO
DELTA_X_RIGHT = 320       # janela lateral à direita do CÓDIGO
DELTA_Y_TOP   = 120       # janela acima do CÓDIGO (título)
DELTA_Y_DOWN  = 220       # janela abaixo do CÓDIGO (preço/linhas)
MARGEM_CROP   = 18        # margem do recorte final

# Regex
RE_CODIGO = re.compile(r"\b([A-Z]{2}\d{3,6})\b")
RE_PRECO  = re.compile(
    r"(?:R?\$?\s*)?(?:\d{1,3}(?:\.\d{3})*|\d+)[,\.]\d{2}",
    flags=re.I
)

# =========================
# Utilitárias
# =========================
def is_noise(txt: str) -> bool:
    if not txt: return True
    if len(txt) < MIN_TEXT_LEN: return True
    # razão de símbolos
    sym = sum(1 for c in txt if not c.isalnum() and c not in "/-,.$R ")
    return (sym / max(len(txt),1)) > MAX_SYM_RATIO

def clean(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "").strip())

def extract_codigo(txt: str) -> str:
    m = RE_CODIGO.search(txt or "")
    return m.group(1) if m else ""

def extract_preco(txt: str) -> str:
    m = RE_PRECO.search(txt or "")
    if not m: return ""
    val = m.group(0)
    # normaliza "R$ 12,90" / "12.90" → "R$ 12,90"
    val = val.replace(" ", "")
    val = val.replace(".", ",") if "," in val else val  # preserva milhar com ponto se não houver vírgula
    # Ajuste simples: se veio "1290" (sem sep), mantém como está
    if "," not in val and "." not in val:
        return f"R$ {val}"
    # Uniformiza vírgula para centavos
    val = val.replace(".", ",")
    return f"R$ {val}"

def bbox_union(boxes):
    minx = min(x for (x,y,w,h) in boxes)
    miny = min(y for (x,y,w,h) in boxes)
    maxx = max(x+w for (x,y,w,h) in boxes)
    maxy = max(y+h for (x,y,w,h) in boxes)
    return (minx, miny, maxx, maxy)

def clamp_bbox(b, img_w, img_h, margem=MARGEM_CROP):
    x1, y1, x2, y2 = b
    x1 = max(x1 - margem, 0)
    y1 = max(y1 - margem, 0)
    x2 = min(x2 + margem, img_w)
    y2 = min(y2 + margem, img_h)
    return (x1, y1, x2, y2)

def in_window(b_code, b, img_w):
    """
    Verifica se o bloco b está dentro da janela do código.
    b_code: dict com x,y,w,h do bloco âncora
    b: bloco candidato
    """
    x1 = b_code["x"] - DELTA_X_LEFT
    x2 = b_code["x"] + b_code["w"] + DELTA_X_RIGHT
    y1 = b_code["y"] - DELTA_Y_TOP
    y2 = b_code["y"] + b_code["h"] + DELTA_Y_DOWN
    return (x1 <= b["x"] <= x2) and (y1 <= b["y"] <= y2)

def normalize_title(raw: str, codigo: str, preco: str) -> str:
    t = clean(raw)
    if codigo: t = t.replace(codigo, "")
    if preco:  t = t.replace(preco.replace("R$","").strip(), "").replace(preco, "")
    t = clean(t)
    # corta "R$" solto / múltiplos espaços
    t = re.sub(r"\bR\$\b", "", t)
    return t

# =========================
# Núcleo por página
# =========================
def processar_pagina(num: int):
    ocr_path = OUT_DIR / f"ocr_page_{num:02d}.json"
    img_path = DATA_DIR / f"page_{num:02d}.jpg"
    if not ocr_path.exists() or not img_path.exists():
        print(f"⚠️  Pular página {num:02d}: OCR ou imagem ausente.")
        return

    with open(ocr_path, "r", encoding="utf-8") as f:
        ocr = json.load(f)

    blocks = ocr.get("blocks", [])
    # Pré-filtro de ruído
    blocks = [
        {
            "text": str(b.get("text","")),
            "x": int(b.get("x",0)), "y": int(b.get("y",0)),
            "w": int(b.get("w",0)), "h": int(b.get("h",0)),
            "conf": int(b.get("conf",0))
        }
        for b in blocks
        if not is_noise(str(b.get("text",""))) and int(b.get("conf",0)) >= CONF_MIN
    ]
    if not blocks:
        print(f"⚠️  Página {num:02d} sem blocos após filtro.")
        out_path = OUT_DIR / f"products_page_{num:02d}.json"
        out_path.write_text("[]", encoding="utf-8")
        return

    # Âncoras = blocos que parecem CÓDIGO
    anchors = [b for b in blocks if extract_codigo(b["text"])]
    if not anchors:
        print(f"⚠️  Página {num:02d} sem âncoras de código.")
        out_path = OUT_DIR / f"products_page_{num:02d}.json"
        out_path.write_text("[]", encoding="utf-8")
        return

    # Ordena âncoras por Y (top-down)
    anchors.sort(key=lambda b: (b["y"], b["x"]))

    img = Image.open(img_path)
    iw, ih = img.size

    produtos = []
    vistos_codigos = set()

    for code_block in anchors:
        codigo = extract_codigo(code_block["text"])
        if not codigo:
            continue
        # Evita duplicar o mesmo código muitas vezes
        if codigo in vistos_codigos:
            continue

        # Coleta blocos na janela
        vizinhos = [b for b in blocks if in_window(code_block, b, iw)]
        if not vizinhos:
            continue

        # Ordena vizinhos em leitura (y, depois x)
        vizinhos.sort(key=lambda b: (b["y"], b["x"]))

        # Texto combinado da janela
        window_text = " ".join(clean(b["text"]) for b in vizinhos)
        preco = extract_preco(window_text)
        titulo = normalize_title(window_text, codigo, preco)

        # Se título ficou vazio, tenta puxar linhas imediatamente acima do código
        if not titulo:
            acima = [b for b in vizinhos if b["y"] < code_block["y"]]
            acima = sorted(acima, key=lambda b: (-b["y"], b["x"]))[:3]  # até 3 linhas acima
            titulo = normalize_title(" ".join(clean(b["text"]) for b in acima), codigo, preco)

        # Se ainda vazio, ignora (provável falso positivo)
        if not (codigo or preco or titulo):
            continue

        # BBox combinada dos vizinhos
        boxes = [(b["x"], b["y"], b["w"], b["h"]) for b in vizinhos]
        x1, y1, x2, y2 = clamp_bbox(bbox_union(boxes), iw, ih, margem=MARGEM_CROP)

        # Crop
        crop = img.crop((x1, y1, x2, y2))
        crop_name = f"page_{num:02d}_{codigo}.jpg"
        crop_path = CROPS_DIR / crop_name
        try:
            crop.save(crop_path)
            img_url = f"/core_pipeline/outputs/crops/{crop_name}"
        except Exception as e:
            img_url = ""

        item = {
            "page": num,
            "codigo": codigo or "",
            "titulo": titulo or "",
            "preco": preco or "",
            "imagem": img_url
        }

        # Deduplicação: se já existe, preferir quem tem preço
        if codigo in vistos_codigos:
            # encontrar existente e comparar
            for k, old in enumerate(produtos):
                if old["codigo"] == codigo:
                    if not old.get("preco") and item.get("preco"):
                        produtos[k] = item
                    break
        else:
            produtos.append(item)
            vistos_codigos.add(codigo)

    # Ordena por posição (page já constante aqui)
    produtos.sort(key=lambda d: (d["codigo"], d["titulo"]))

    out_path = OUT_DIR / f"products_page_{num:02d}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    print(f"✅ Página {num:02d} → {len(produtos)} produtos (âncora por código)")

# =========================
# Execução
# =========================
def main():
    print("🚀 Montagem (âncora por código) – Passo B")
    paginas = sorted([int(p.stem.split("_")[1]) for p in DATA_DIR.glob("page_*.jpg")])
    for num in paginas:
        processar_pagina(num)
    print("🏁 Passo B finalizado.")

if __name__ == "__main__":
    main()
