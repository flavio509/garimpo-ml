"""
Garimpo ML – Reconstrução do pipeline OCR por página (v2025-11-12)
------------------------------------------------------------------
Lê as imagens page_XX.jpg, executa OCR com pytesseract, limpa o texto
e gera JSONs products_page_XX.json prontos para renderização.
"""

import os, re, json, pytesseract
from pathlib import Path
from PIL import Image
from datetime import datetime

# ============================================================
# 🔹 Caminhos base
# ============================================================
BASE_DIR = Path("/home/ubuntu/garimpo-ml")
DATA_DIR = BASE_DIR / "core_pipeline" / "data" / "TTBRASIL_20251112" / "outputs"
OUT_DIR = BASE_DIR / "core_pipeline" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 🔹 Funções utilitárias
# ============================================================
def limpar_texto(txt: str) -> str:
    """Remove espaços extras e caracteres estranhos."""
    return re.sub(r"\s+", " ", txt).strip()

def extrair_campos_linha(linha: str):
    """
    Extrai código, título e preço de uma linha OCR.
    Regras derivadas da sessão 2810.
    """
    linha = limpar_texto(linha)
    if not linha:
        return None

    # Código do produto (CT, CX, etc.)
    codigo = None
    m = re.search(r"\b([A-Z]{2}\d{3,6})\b", linha)
    if m:
        codigo = m.group(1)

    # Preço (R$ 99,90 ou 12.90)
    preco = None
    m2 = re.search(r"(R?\$?\s*\d+[.,]\d{2})", linha)
    if m2:
        preco = m2.group(1).replace(" ", "").replace(",", ".")

    # Título: o que sobra
    titulo = linha
    for pat in [codigo, preco]:
        if pat:
            titulo = titulo.replace(pat, "")
    titulo = limpar_texto(titulo)

    if not (codigo or preco or titulo):
        return None
    return {"codigo": codigo or "", "titulo": titulo, "preco": preco or ""}

# ============================================================
# 🔹 OCR por página
# ============================================================
def processar_pagina(num: int):
    """
    Executa OCR em page_XX.jpg e gera products_page_XX.json.
    """
    img_path = DATA_DIR / f"page_{num:02d}.jpg"
    if not img_path.exists():
        print(f"⚠️  Imagem não encontrada: {img_path}")
        return

    print(f"📄 Processando página {num:02d}...")

    # OCR básico
    img = Image.open(img_path)
    raw_text = pytesseract.image_to_string(img, lang="por+eng")

    # Quebra por linhas e aplica parser
    produtos = []
    for linha in raw_text.split("\n"):
        item = extrair_campos_linha(linha)
        if item:
            item["page"] = num
            item["imagem"] = f"/core_pipeline/data/TTBRASIL_20251112/outputs/page_{num:02d}.jpg"
            produtos.append(item)

    # Salva JSON
    out_path = OUT_DIR / f"products_page_{num:02d}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    print(f"✅ Página {num:02d} concluída → {out_path}")

# ============================================================
# 🔹 Execução principal
# ============================================================
def main():
    print("🚀 Iniciando reconstrução OCR → products_page_XX.json")
    paginas = sorted([int(p.stem.split("_")[1]) for p in DATA_DIR.glob("page_*.jpg")])
    for num in paginas:
        processar_pagina(num)
    print(f"🏁 Processo finalizado às {datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()
