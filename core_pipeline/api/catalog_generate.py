"""
Garimpo ML – Geração de HTML de Catálogo (v2025-11-10)
-------------------------------------------------------
Une JSONs normalizados + OCR e gera HTML paginado
para revisão em /out/catalog_review.html
"""

import os
import json
import datetime

BASE_DIR = "/home/ubuntu/garimpo-ml"
OUTPUTS_DIR = os.path.join(BASE_DIR, "core_pipeline/outputs")
OUT_DIR = os.path.join(BASE_DIR, "out")
os.makedirs(OUT_DIR, exist_ok=True)

def gerar_html():
    html_path = os.path.join(OUT_DIR, "catalog_review.html")
    paginas = sorted([f for f in os.listdir(OUTPUTS_DIR) if f.startswith("normalized_page_") and f.endswith(".json")])

    conteudo = [
        "<html><head><meta charset='utf-8'><title>Catálogo – Garimpo ML</title>",
        "<style>body{font-family:Arial;margin:20px;} .produto{border:1px solid #ccc;padding:10px;margin:8px;border-radius:8px;} .pag{margin-top:40px;border-top:2px solid #999;}</style>",
        "</head><body><h1>Catálogo Extraído</h1>"
    ]

    for idx, fn in enumerate(paginas, 1):
        with open(os.path.join(OUTPUTS_DIR, fn), "r", encoding="utf-8") as f:
            itens = json.load(f)
        conteudo.append(f"<div class='pag'><h2>Página {idx}</h2>")
        for p in itens:
            titulo = p.get("ocr_title") or p.get("title") or ""
            preco = p.get("ocr_price") or p.get("price") or ""
            codigo = p.get("ocr_code") or p.get("code") or ""
            conf = p.get("ocr_confidence", 0)
            conteudo.append(f"<div class='produto'><b>{titulo}</b><br>💲 {preco}<br>🔢 {codigo}<br>📈 conf={conf}</div>")
        conteudo.append("</div>")

    conteudo.append(f"<p>Gerado em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(conteudo))
    print(f"[GarimpoML] HTML gerado em {html_path}")
    return html_path

if __name__ == "__main__":
    gerar_html()
