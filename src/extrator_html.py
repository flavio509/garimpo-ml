import os
import re
import json
from bs4 import BeautifulSoup

HTML_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'html')
PENDING_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'pending')
JSON_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'json')

os.makedirs(JSON_FOLDER, exist_ok=True)

def extrair_produtos_de_html(html_path):
    """Extrai título, preço e imagem de um HTML de catálogo"""
    produtos = []

    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f, 'html.parser')

    for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'span']):
        texto = tag.get_text(strip=True)
        if not texto or len(texto) < 4:
            continue

        # Detecta preço
        preco = re.findall(r'R\$ ?\d+[.,]?\d*', texto)
        if preco:
            produtos.append({
                "titulo": texto.replace(preco[0], '').strip(),
                "preco": preco[0],
                "imagem": None
            })

    # Associa imagens (opcional, se houver tags <img>)
    imagens = [img['src'] for img in soup.find_all('img') if img.get('src')]
    for i, produto in enumerate(produtos):
        if i < len(imagens):
            produto['imagem'] = imagens[i]

    # Salva em JSON
    nome_base = os.path.splitext(os.path.basename(html_path))[0]
    json_path = os.path.join(JSON_FOLDER, f"{nome_base}.json")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    print(f"Extração concluída: {len(produtos)} produtos encontrados.")
    print(f"Arquivo JSON salvo em: {json_path}")
    return json_path
