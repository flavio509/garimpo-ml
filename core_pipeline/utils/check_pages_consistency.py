import os
from PIL import Image

def verificar_paginas(base_dir="/home/ubuntu/garimpo-ml/data/pages"):
    """
    Verifica a consistência das páginas convertidas do PDF.
    Regras:
      - Deve haver exatamente 33 arquivos JPG.
      - Nomes: page_01.jpg até page_33.jpg
      - Cada imagem deve ter 300 dpi.
    Retorna um dicionário com o status detalhado.
    """
    expected_count = 33
    files = sorted([f for f in os.listdir(base_dir) if f.lower().endswith(".jpg")])
    report = {"total_encontradas": len(files), "faltantes": [], "dpi_erradas": []}

    # Verificar quantidade e nomes esperados
    for i in range(1, expected_count + 1):
        fname = f"page_{i:02}.jpg"
        if fname not in files:
            report["faltantes"].append(fname)

    # Verificar DPI de cada imagem
    for f in files:
        fpath = os.path.join(base_dir, f)
        try:
            with Image.open(fpath) as img:
                dpi = img.info.get("dpi", (0, 0))[0]
                if dpi < 290 or dpi > 310:
                    report["dpi_erradas"].append((f, dpi))
        except Exception as e:
            report["dpi_erradas"].append((f, f"erro: {e}"))

    report["ok"] = (
        report["total_encontradas"] == expected_count
        and not report["faltantes"]
        and not report["dpi_erradas"]
    )
    return report
