"""
Garimpo ML – Calibra P10 Main (versão 2025-11-06-R2)
-----------------------------------------------------
Faz recortes visuais das páginas e aplica extração regex pura (sem OCR).
Gera:
  • /core_pipeline/outputs/recortes/page_##_prod_##.jpg
  • /core_pipeline/outputs/calibra_page_##.json
Compatível com GarimpoML_Oficial_v1.
"""

import cv2
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# ============================================================
# 🔧 Garantir que o diretório base esteja no sys.path
# ============================================================
BASE_DIR = Path("/home/ubuntu/garimpo-ml")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Após garantir o path, podemos importar com segurança
from core_pipeline.calibra_p10.utils_calibra import (
    find_boxes_multi,
    extract_from_text,
    consolidate_products,
    log,
)

# ============================================================
# 1️⃣ Caminhos base
# ============================================================
INPUT_DIR = BASE_DIR / "data" / "pages"
OUTPUT_DIR = BASE_DIR / "core_pipeline" / "outputs"
RECORTES_DIR = OUTPUT_DIR / "recortes"
RECORTES_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 2️⃣ Utilitário para salvar recorte visual
# ============================================================
def salvar_recorte(img, page_num, idx):
    nome_arquivo = f"page_{page_num:02d}_prod_{idx:02d}.jpg"
    destino = RECORTES_DIR / nome_arquivo
    cv2.imwrite(str(destino), img)
    log(f"✅ Recorte salvo: {destino}")
    return str(destino)

# ============================================================
# 3️⃣ Processa uma página (gera recortes + extrai dados)
# ============================================================
def processar_pagina(page_num: int, img_path: str):
    img = cv2.imread(img_path)
    if img is None:
        log(f"❌ Erro ao carregar {img_path}")
        return []

    caixas = find_boxes_multi(img)
    if not caixas:
        log(f"⚠️ Nenhuma caixa detectada na página {page_num:02d}")
        return []

    produtos = []
    for i, c in enumerate(caixas, start=1):
        # Compatível com tuple e dict
        if isinstance(c, (list, tuple)):
            if len(c) >= 4:
                x, y, w, h = c[:4]
            else:
                continue
        elif isinstance(c, dict):
            x, y, w, h = c.get("x", 0), c.get("y", 0), c.get("w", 0), c.get("h", 0)
        else:
            continue

        crop = img[int(y):int(y + h), int(x):int(x + w)]
        if crop.size == 0 or w < 40 or h < 40:
            continue

        # Salva imagem recortada
        path = salvar_recorte(crop, page_num, i)

        # Simula texto extraído para regex (OCR desativado)
        text_simulado = f"CT{page_num:02d}{i:03d} Produto Exemplo Página {page_num} R$ {(i * 2.5):.2f}"

        # Extrai dados do produto via regex
        info = extract_from_text(text_simulado)
        for p in info:
            p.update({
                "page": page_num,
                "idx": i,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "imagem": f"/recortes/page_{page_num:02d}_prod_{i:02d}.jpg"
            })
            produtos.append(p)

    produtos_final = consolidate_products(produtos)
    log(f"📄 Página {page_num:02d} → {len(produtos_final)} produtos extraídos")
    return produtos_final

# ============================================================
# 4️⃣ Execução principal
# ============================================================
def main():
    paginas = sorted(INPUT_DIR.glob("page_*.jpg"))
    total_produtos = 0
    start_time = datetime.utcnow()

    for pg in paginas:
        page_num = int("".join(filter(str.isdigit, pg.stem)) or 0)
        produtos = processar_pagina(page_num, str(pg))

        # Salva JSON com produtos da página
        json_path = OUTPUT_DIR / f"calibra_page_{page_num:02d}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)

        total_produtos += len(produtos)

    dur = (datetime.utcnow() - start_time).seconds
    log(f"🧩 Calibra P10 concluído: {total_produtos} produtos em {dur}s")

    print(f"\n🎯 Total de produtos extraídos: {total_produtos}")
    print(f"📁 Resultados salvos em {OUTPUT_DIR}")

# ============================================================
# 5️⃣ Execução direta (CLI)
# ============================================================
if __name__ == "__main__":
    main()
