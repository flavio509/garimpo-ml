import os, sys, json, datetime

# --- Corrige caminho raiz do projeto (nível superior) ---
BASE_DIR = "/home/ubuntu/garimpo-ml"
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from core_pipeline.calibra_p10.utils_calibra import extract_from_text

"""
===========================================================
TESTE UNITÁRIO – EXTRACT_FROM_TEXT (regex pura)
Garimpo ML – Calibração P10
Data: {}
===========================================================
""".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# === 1️⃣ Entrada de teste simulada (extraída da página 4 do catálogo TTBRASIL) ===
sample_text = """
Borrifador Diamante Sortido CT2092
Capacidade: 500ML
Embalagem: Solapa
R$ 4,70 Material: Pet

Balde Multiuso 12L GT3010
Medidas: 32x25cm
Cores: Azul/Vermelho
R$ 12,90

Garrafa Térmica Slim 1L TT5020
Cor: Branca
R$ 29,90
"""

# === 2️⃣ Execução da função ===
produtos = extract_from_text(sample_text)

# === 3️⃣ Exibição dos resultados ===
print("=== RESULTADO DOS PRODUTOS DETECTADOS ===")
for p in produtos:
    print(f"Título: {p.get('titulo')}")
    print(f"Código: {p.get('codigo')}")
    print(f"Preço:  {p.get('preco')}")
    print("-" * 60)

# === 4️⃣ Exporta resultado em JSON (para depuração futura) ===
out_path = "/home/ubuntu/garimpo-ml/core_pipeline/outputs/test_extract_output.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(produtos, f, ensure_ascii=False, indent=2)

print(f"\nArquivo salvo em: {out_path}")
