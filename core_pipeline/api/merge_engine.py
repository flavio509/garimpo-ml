"""
Garimpo ML – Merge Final ( v2025-11-12 )
-----------------------------------------
Une todos os products_page_XX.json em um único merged_output.json,
gera merge_summary.json e imprime resumo no stdout.
Executado automaticamente pela rota /meuapp/catalog-api/merge.
"""

import os, json
from datetime import datetime
from pathlib import Path

# =========================
# Caminhos
# =========================
BASE_DIR  = Path("/home/ubuntu/garimpo-ml")
OUT_DIR   = BASE_DIR / "core_pipeline" / "outputs"
MERGED    = OUT_DIR / "merged_output.json"
SUMMARY   = OUT_DIR / "merge_summary.json"

# =========================
# Núcleo do merge
# =========================
def executar_merge():
    print("🚀  Iniciando Passo C – Merge Final de produtos")
    pages = sorted(
        [p for p in OUT_DIR.glob("products_page_*.json")],
        key=lambda f: int(f.stem.split("_")[-1])
    )

    all_products = []
    summary = {"paginas": {}, "total_produtos": 0}

    for page_file in pages:
        page_num = int(page_file.stem.split("_")[-1])
        try:
            data = json.loads(page_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Falha ao ler {page_file.name}: {e}")
            continue

        qtd = len(data)
        summary["paginas"][f"{page_num:02d}"] = qtd
        summary["total_produtos"] += qtd

        for p in data:
            p["page"] = page_num
            all_products.append(p)

        print(f"✅  Página {page_num:02d} → {qtd} produtos fundidos")

    # Ordena e salva o merged
    all_products.sort(key=lambda d: (d.get("page", 0), d.get("codigo", "")))
    MERGED.write_text(json.dumps(all_products, ensure_ascii=False, indent=2), encoding="utf-8")

    summary.update({
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "arquivos_fonte": [p.name for p in pages],
        "arquivo_saida": MERGED.name
    })
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("🏁  Merge Final concluído com sucesso.")
    print(f"📄  merged_output.json → {len(all_products)} produtos totais.")
    print(f"📊  merge_summary.json gerado com detalhamento por página.")
    return summary

# =========================
# Execução direta
# =========================
if __name__ == "__main__":
    executar_merge()
