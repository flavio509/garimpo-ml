from pdf2image import convert_from_path
from pathlib import Path
import os

PDF_PATH = Path("data/uploads/TABELA_TTBRASIL.pdf")
OUT_DIR = Path("data/pages")
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"📘 Convertendo {PDF_PATH.name} em imagens...")
pages = convert_from_path(PDF_PATH, dpi=200)

for i, page in enumerate(pages, start=1):
    out_file = OUT_DIR / f"page_{i:02d}.jpg"
    page.save(out_file, "JPEG")
    print(f"✅ Página {i:02d} salva em {out_file}")

print(f"🎯 Conversão concluída com sucesso ({len(pages)} páginas).")
