import json, re
from pathlib import Path
from collections import defaultdict

PROD_JSON = Path("core_pipeline/outputs/ttbrasil_products.json")
OUT_REPORT = Path("core_pipeline/outputs/relatorio_ocr_consistencia.txt")

print("📊 Gerando relatório de consistência OCR...")

if not PROD_JSON.exists():
    raise FileNotFoundError(PROD_JSON)

data = json.load(open(PROD_JSON, "r", encoding="utf-8"))
por_pagina = defaultdict(list)
erros = []

for item in data:
    pg = str(item.get("page", "?"))
    txt = item.get("text", "")
    cod = re.search(r"CT\d{3,5}", txt)
    pre = re.search(r"R\$ ?\d+[.,]?\d*", txt)
    cod = cod.group() if cod else "—"
    pre = pre.group() if pre else "—"
    item["codigo"], item["preco"] = cod, pre
    por_pagina[pg].append(item)
    if cod == "—" or pre == "—":
        erros.append(item)

rel = [f"Total produtos: {len(data)}", f"Páginas: {len(por_pagina)}"]
for pg, itens in por_pagina.items():
    rel.append(f"- Página {pg}: {len(itens)} produtos")
OUT_REPORT.write_text("\n".join(rel), encoding="utf-8")
print(f"✅ Relatório salvo em {OUT_REPORT}")
