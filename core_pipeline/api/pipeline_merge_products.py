import json
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("/home/ubuntu/garimpo-ml/core_pipeline/outputs")
NORMALIZED_PATTERN = "normalized_page_*.json"
OUTPUT_PREFIX = "products_page_"

def merge_products():
    """
    Consolida os arquivos normalized_page_##.json em products_page_##.json.
    Corrige automaticamente os caminhos de imagem para /recortes/.
    """
    print("🔄 Iniciando consolidação dos arquivos normalizados...")

    normalized_files = sorted(
        BASE_DIR.glob(NORMALIZED_PATTERN),
        key=lambda p: int(''.join(filter(str.isdigit, p.stem)) or 0)
    )

    if not normalized_files:
        print("❌ Nenhum arquivo normalized_page_XX.json encontrado.")
        return

    total_itens = 0
    page_summary = []

    for nf in normalized_files:
        page_num = int(''.join(filter(str.isdigit, nf.stem)) or 0)
        with nf.open("r", encoding="utf-8") as f:
            items = json.load(f)

        products = []
        for i, item in enumerate(items, start=1):
            # Corrige o caminho da imagem se estiver em /crops/
            img_path = item.get("imagem", "")
            if img_path and "/crops/" in img_path:
                # Converte para /recortes/page_##_prod_##.jpg
                img_path = f"/recortes/page_{page_num:02d}_prod_{i:02d}.jpg"

            prod = {
                "codigo": item.get("codigo", "").strip(),
                "titulo": item.get("titulo", "").strip(),
                "preco": item.get("preco", "").strip(),
                "imagem": img_path or None,
                "page": page_num,
                "timestamp": datetime.utcnow().isoformat(timespec="seconds")
            }
            products.append(prod)

        # Salva o arquivo products_page_##.json
        out_path = BASE_DIR / f"{OUTPUT_PREFIX}{page_num:02d}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        total_itens += len(products)
        page_summary.append((page_num, len(products)))
        print(f"✅ Página {page_num:02d}: {len(products)} produtos consolidados → {out_path.name}")

    # Gera log final
    log_path = BASE_DIR / "log_merge_products.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write("LOG MERGE PRODUCTS – " + str(datetime.utcnow()) + "\n\n")
        for pg, n in page_summary:
            f.write(f"Página {pg:02d}: {n} produtos\n")
        f.write(f"\nTotal consolidado: {total_itens} produtos\n")

    print(f"\n🎯 Consolidação concluída com sucesso. Total: {total_itens} produtos.")
    print(f"📄 Log salvo em: {log_path}")

if __name__ == "__main__":
    merge_products()
