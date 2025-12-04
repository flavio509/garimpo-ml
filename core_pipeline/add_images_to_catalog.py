import json
import re
from pathlib import Path

# Caminhos base
base_dir = Path("/home/ubuntu/garimpo-ml/core_pipeline/outputs")
json_file = base_dir / "normalized_page_01_TEST.json"
html_file = base_dir / "catalogo_interativo.html"
output_file = base_dir / "catalogo_interativo_com_imagens.html"

# URL base do site
BASE_URL = "https://marcasshop.com.br/core_pipeline/outputs"

# Carrega os produtos do JSON
with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Lê o HTML original
html = html_file.read_text(encoding="utf-8")

# Para cada produto, tenta inserir a imagem antes do campo de código correspondente
for produto in data:
    codigo = produto.get("codigo", "").strip()
    imagem = produto.get("imagem", "").strip()

    if not codigo or not imagem:
        continue

    # Garante que o caminho seja absoluto
    if not imagem.startswith("http"):
        imagem = f"{BASE_URL}{imagem if imagem.startswith('/') else '/' + imagem}"

    # Cria a tag da imagem
    tag_img = f'<img src="{imagem}" alt="{codigo}" style="max-width:80px; max-height:80px; border-radius:6px; margin-right:10px;">'

    # Expressão para localizar o campo do código
    padrao = rf'(<input[^>]+value="{re.escape(codigo)}"[^>]*>)'
    novo_html = rf'{tag_img}\1'

    # Substitui apenas a primeira ocorrência
    html, count = re.subn(padrao, novo_html, html, count=1)
    if count > 0:
        print(f"[OK] Imagem adicionada para {codigo} → {imagem}")

# Salva o novo HTML
output_file.write_text(html, encoding="utf-8")

print(f"\n✅ Catálogo atualizado salvo em: {output_file}")
print("Abra no navegador para verificar as imagens.")
