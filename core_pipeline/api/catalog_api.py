"""
Garimpo ML – API de Catálogo (v2025-11-12-D)
---------------------------------------------
Exibe e permite revisão do catálogo consolidado.
Fonte: merged_output.json (gerado no Passo C).
"""

import os, json, math
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify

# ============================================================
# 🔹 Blueprint e caminhos
# ============================================================
catalog_bp = Blueprint("catalog_bp", __name__, url_prefix="/meuapp/catalog-api")

BASE_DIR     = Path("/home/ubuntu/garimpo-ml")
OUTPUTS_DIR  = BASE_DIR / "core_pipeline" / "outputs"
MERGED_FILE  = OUTPUTS_DIR / "merged_output.json"

# ============================================================
# 🔹 Função de utilidade
# ============================================================
def carregar_catalogo():
    if not MERGED_FILE.exists():
        return []
    with open(MERGED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# 🔹 ROTA: /review  → interface de revisão paginada
# ============================================================
@catalog_bp.route("/review", methods=["GET"])
def review_catalog():
    produtos = carregar_catalogo()
    if not produtos:
        return "<h2>Nenhum produto encontrado. Execute o merge primeiro.</h2>"

    page = int(request.args.get("page", 1))
    por_pagina = 10
    total_paginas = math.ceil(len(produtos) / por_pagina)

    inicio = (page - 1) * por_pagina
    fim = inicio + por_pagina
    subset = produtos[inicio:fim]

    catalogos_disponiveis = ["merged_output.json"]

    return render_template(
        "reviews.html",
        produtos=subset,
        page=page,
        total_paginas=total_paginas,
        catalogos_disponiveis=catalogos_disponiveis,
        catalogo_atual="merged_output.json"
    )

# ============================================================
# 🔹 ROTA: /update  → salva edições no merged_output.json
# ============================================================
@catalog_bp.route("/update", methods=["POST"])
def atualizar_produtos():
    try:
        dados = request.get_json(force=True)
        if not isinstance(dados, list):
            return jsonify({"ok": False, "erro": "Formato inválido (esperado lista)"}), 400

        produtos = carregar_catalogo()
        idx = {p.get("codigo"): i for i, p in enumerate(produtos) if p.get("codigo")}

        atualizados = 0
        for item in dados:
            cod = item.get("codigo")
            if cod and cod in idx:
                produtos[idx[cod]].update(item)
                atualizados += 1

        MERGED_FILE.write_text(
            json.dumps(produtos, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return jsonify({"ok": True, "atualizados": atualizados})

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

# ============================================================
# 🔹 ROTA: /remove  → remove produto do merged_output.json
# ============================================================
@catalog_bp.route("/remove", methods=["POST"])
def remover_produto():
    try:
        cod = request.get_json(force=True).get("codigo")
        if not cod:
            return jsonify({"ok": False, "erro": "Código ausente"}), 400

        produtos = carregar_catalogo()
        novos = [p for p in produtos if p.get("codigo") != cod]

        MERGED_FILE.write_text(
            json.dumps(novos, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
# teste de modificação
