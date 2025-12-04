import json
import re
from pathlib import Path
from datetime import datetime


BASE_DIR = Path("/home/ubuntu/garimpo-ml")
OUT_BASE = BASE_DIR / "core_pipeline" / "outputs"


def assemble(upload_id: str) -> None:
    out_dir = OUT_BASE / upload_id
    if not out_dir.exists():
        print(f"❌ Diretório de saída não encontrado: {out_dir}")
        return

    norm_files = sorted(
        out_dir.glob("normalized_page_*.json"),
        key=lambda p: int(re.findall(r"\d+", p.stem)[0]),
    )

    print(f"📦 Consolidando arquivos normalizados em catalogo_base.json ({upload_id})...")

    all_items = []

    for nf in norm_files:
        with nf.open("r", encoding="utf-8") as f:
            produtos = json.load(f)

        for p in produtos:
            item = {
                "page": p.get("page"),
                "codigo": p.get("codigo", "") or "",
                "titulo": p.get("titulo", "") or "",
                "preco": p.get("preco", "") or "",
                "imagem": p.get("imagem", "") or "",
                "fonte": p.get("fonte", "crops_auto"),
            }
            all_items.append(item)

        print(f"✅ Página {p.get('page', '?')} → {len(produtos)} produtos adicionados")

    saida = out_dir / "catalogo_base.json"
    with saida.open("w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    log_path = out_dir / "log_assemble_products.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write("LOG ASSEMBLE PRODUCTS – " + str(datetime.now()) + "\n\n")
        f.write(f"Total de produtos: {len(all_items)}\n")
        f.write(f"Arquivos mesclados: {[p.name for p in norm_files]}\n")

    print(f"🎯 Merge concluído → {saida}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("❌ Uso: python3 core_pipeline/assembler/assemble_products.py <upload_id>")
        raise SystemExit(1)

    assemble(sys.argv[1])