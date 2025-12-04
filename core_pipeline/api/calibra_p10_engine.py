"""
Calibra P10 Engine Interno – Garimpo ML (2025-11-07)
----------------------------------------------------
Extração de códigos, títulos e preços a partir de imagens JPG
usando regex e filtragem leve. Compatível com pipeline oficial.
"""

import os, re, json, cv2, numpy as np

def run_calibra_p10(pages_dir, outputs_dir, log_list):
    regex_codigo = r"CT\d{3,5}"
    regex_preco = r"R?\$ ?\d{1,3}(?:\.\d{3})*,\d{2}"
    regex_titulo = r"[A-Z][A-Z0-9\s\-]{5,}"

    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir, exist_ok=True)

    for fname in sorted(os.listdir(pages_dir)):
        if not fname.lower().endswith(".jpg"):
            continue
        page_num = os.path.splitext(fname)[0].split("_")[-1]
        img_path = os.path.join(pages_dir, fname)
        out_json = os.path.join(outputs_dir, f"calibra_page_{page_num}.json")

        log_list.append(f"→ Processando {fname}\n")

        try:
            img = cv2.imread(img_path)
            if img is None:
                log_list.append(f"⚠️ Falha ao ler {fname}\n")
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.medianBlur(gray, 3)
            _, th = cv2.threshold(blur, 180, 255, cv2.THRESH_BINARY)
            text = " ".join(re.findall(r"[A-Z0-9\.\,\$\/\-]+", str(th)))

            codigos = re.findall(regex_codigo, text)
            precos = re.findall(regex_preco, text)
            titulos = re.findall(regex_titulo, text)

            produtos = []
            for i, codigo in enumerate(codigos):
                produto = {
                    "codigo": codigo,
                    "titulo": titulos[i] if i < len(titulos) else "",
                    "preco": precos[i] if i < len(precos) else ""
                }
                produtos.append(produto)

            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(produtos, f, indent=2, ensure_ascii=False)

            log_list.append(f"✔️ calibra_page_{page_num}.json salvo ({len(produtos)} produtos)\n")

        except Exception as e:
            log_list.append(f"❌ Erro na página {fname}: {e}\n")
