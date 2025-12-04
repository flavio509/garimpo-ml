import json
import re
import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# 🔧 Diretório base
# ============================================================

DEFAULT_ROOT = Path("core_pipeline/outputs")


def _resolve_out_dir() -> Path:
    """
    Resolve diretório do job:
    - Sem argumentos → core_pipeline/outputs
    - Com argumento → core_pipeline/outputs/<JOB_ID>
    """
    if len(sys.argv) >= 2:
        job_id = (sys.argv[1] or "").strip()
        if job_id:
            return DEFAULT_ROOT / job_id
    return DEFAULT_ROOT


OUT_DIR = _resolve_out_dir()


# ============================================================
# 🔧 Carregar todos normalized_page_XX.json
# ============================================================

def load_normalized_pages() -> list:
    files = sorted(
        OUT_DIR.glob("normalized_page_*.json"),
        key=lambda p: int(re.findall(r"\d+", p.stem)[0])
    )

    all_items = []

    for f in files:
        try:
            with f.open("r", encoding="utf-8") as fp:
                itens = json.load(fp)
                if isinstance(itens, list):
                    all_items.extend(itens)
        except Exception:
            continue

    return all_items


# ============================================================
# 🔧 Normalização final dos produtos
# ============================================================

def clean_item(prod: dict) -> dict:
    """
    Sanitiza campos e garante estrutura consistente.
    """
    return {
        "page": prod.get("page", 0),
        "codigo": (prod.get("codigo") or "").strip(),
        "titulo": (prod.get("titulo") or "").strip(),
        "preco": (prod.get("preco") or "").replace(" ", ""),
        "imagem": prod.get("imagem", ""),
        "fonte": prod.get("fonte", "crops_auto"),
        "original": prod.get("original", "")
    }


# ============================================================
# 🔧 Salvamento do catálogo final
# ============================================================

def save_catalog(items: list):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final_path = OUT_DIR / "catalogo_base.json"

    with final_path.open("w", encoding="utf-8") as fp:
        json.dump(items, fp, ensure_ascii=False, indent=2)

    return final_path


# ============================================================
# 🔧 MAIN
# ============================================================

def main():
    print(f"📦 Montando catálogo final a partir de: {OUT_DIR.resolve()}")

    items = load_normalized_pages()
    print(f"🔍 {len(items)} itens coletados das páginas normalizadas")

    cleaned = [clean_item(it) for it in items]

    # Ordenação: por página → código
    cleaned = sorted(cleaned, key=lambda x: (x["page"], x["codigo"]))

    path = save_catalog(cleaned)

    print(f"✅ Catálogo final salvo em: {path.resolve()}")
    print(f"📌 Total de produtos: {len(cleaned)}")
    print("🎯 assemble_products concluído.")


if __name__ == "__main__":
    main()
