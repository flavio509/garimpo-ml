import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
import os
from bs4 import BeautifulSoup

# --- Caminhos base ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "../data"
HTML_DIR = DATA_DIR / "html"
IMG_DIR = DATA_DIR / "img"
TMP_DIR = DATA_DIR / "tmp"

for d in [HTML_DIR, IMG_DIR, TMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def extrair_texto_ocr(pdf_path):
    """
    Extrai texto via OCR (Tesseract) de cada página.
    Retorna uma string concatenada com o texto reconhecido.
    """
    print("[🔍] Aplicando OCR nas páginas do PDF...")
    texto_total = ""
    pages = convert_from_path(pdf_path, dpi=200, output_folder=TMP_DIR)

    for i, page in enumerate(pages):
        img_temp = TMP_DIR / f"page_{i+1}.png"
        page.save(img_temp, "PNG")
        texto = pytesseract.image_to_string(Image.open(img_temp), lang="por")
        texto_total += f"\n--- Página {i+1} ---\n{texto}"

    return texto_total


def extrair_produtos(pdf_path):
    """
    Extrai produtos com base em texto + OCR + imagens.
    Retorna lista de dicionários.
    """
    produtos = []
    pdf_path = Path(pdf_path)
    texto_pdf = ""

    # Tenta extrair texto com pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pagina in pdf.pages:
                texto_pdf += (pagina.extract_text() or "") + "\n"
    except Exception as e:
        print(f"[!] Falha no pdfplumber: {e}")

    # Se não encontrou texto, aplica OCR
    if len(texto_pdf.strip()) < 20:
        texto_pdf = extrair_texto_ocr(pdf_path)

    # Detecta padrões de produtos
    for linha in texto_pdf.split("\n"):
        if "R$" in linha:
            partes = linha.split("R$")
            titulo = partes[0].strip()
            preco = "R$" + partes[1].strip() if len(partes) > 1 else "R$ ?"
            produtos.append({
                "titulo": titulo,
                "preco": preco,
                "imagem": None,
                "descricao": ""
            })

    # Extrai imagens reais
    with fitz.open(pdf_path) as pdf_img:
        for i, page in enumerate(pdf_img):
            for j, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_image = pdf_img.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_filename = f"{pdf_path.stem}_p{i+1}_{j}.{image_ext}"
                image_path = IMG_DIR / image_filename
                with open(image_path, "wb") as f:
                    f.write(image_bytes)

                # Vincula imagem ao produto se possível
                if j < len(produtos):
                    produtos[j]["imagem"] = f"../img/{image_filename}"

    return produtos


def gerar_html(nome_pdf, produtos):
    modelo_path = HTML_DIR / "modelo_base.html"
    with open(modelo_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    body = soup.find("body")
    body.clear()

    h1 = soup.new_tag("h1")
    h1.string = f"Catálogo Convertido – {nome_pdf}"
    body.append(h1)

    if not produtos:
        aviso = soup.new_tag("p")
        aviso.string = "Nenhum produto identificado no catálogo."
        body.append(aviso)
    else:
        for p in produtos:
            div_prod = soup.new_tag("div", **{"class": "produto"})
            img = soup.new_tag("img", src=p["imagem"] or "sem-imagem.jpg", **{"class": "imagem", "alt": p["titulo"]})
            detalhes = soup.new_tag("div", **{"class": "detalhes"})

            titulo = soup.new_tag("h2", **{"class": "titulo"})
            titulo.string = p["titulo"]

            preco = soup.new_tag("span", **{"class": "preco"})
            preco.string = p["preco"]

            desc = soup.new_tag("p", **{"class": "descricao"})
            desc.string = p["descricao"]

            detalhes.append(titulo)
            detalhes.append(preco)
            detalhes.append(desc)

            div_prod.append(img)
            div_prod.append(detalhes)
            body.append(div_prod)

    saida = HTML_DIR / f"{nome_pdf}.html"
    with open(saida, "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    print(f"[✔] HTML gerado com sucesso: {saida}")
    return saida


def main():
    pdf_path = input("Caminho completo do PDF: ").strip()
    if not os.path.exists(pdf_path):
        print(f"[x] Arquivo não encontrado: {pdf_path}")
        return

    nome_pdf = Path(pdf_path).stem
    produtos = extrair_produtos(pdf_path)
    if not produtos:
        print("[!] Nenhum produto encontrado, mesmo após OCR.")
    else:
        print(f"[✔] {len(produtos)} produtos identificados.")
    gerar_html(nome_pdf, produtos)


if __name__ == "__main__":
    main()
