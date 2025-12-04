import os
import subprocess
import glob
import traceback


def _find_pdftoppm() -> str | None:
    """
    Localiza o binário pdftoppm. Usa PATH do sistema como fallback.
    """
    candidates = [
        "/usr/bin/pdftoppm",
        "/usr/local/bin/pdftoppm",
        "/usr/share/poppler-utils/pdftoppm",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    # fallback: confiar no PATH
    return "pdftoppm"


def convert_pdf_to_jpg(pdf_path, output_dir, dpi=300):
    """
    Converte um PDF em páginas JPG numeradas usando diretamente o pdftoppm.

    Retorno:
        {
          "status": "success" | "error",
          "pages": ["page_01.jpg", ...],
          "page_count": int,
          "output_dir": str,
          "pdf_path": str,
          "error": str | None
        }
    """

    result = {
        "status": "error",
        "pages": [],
        "page_count": 0,
        "output_dir": output_dir,
        "pdf_path": pdf_path,
        "error": None,
    }

    try:
        if not os.path.exists(pdf_path):
            result["error"] = f"Arquivo PDF não encontrado: {pdf_path}"
            return result

        os.makedirs(output_dir, exist_ok=True)

        pdftoppm_bin = _find_pdftoppm()
        if not pdftoppm_bin:
            result["error"] = "Binário pdftoppm não encontrado"
            return result

        # Prefixo dos arquivos gerados (pdftoppm cria page-1.jpg, page-2.jpg, ...)
        prefix = os.path.join(output_dir, "page")

        # Chamada direta ao pdftoppm
        # -jpeg -> gera JPG
        # -r <dpi> -> resolução
        cmd = [
            pdftoppm_bin,
            "-jpeg",
            "-r",
            str(dpi),
            pdf_path,
            prefix,
        ]

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if proc.returncode != 0:
            # Erro real na conversão
            result["error"] = f"pdftoppm falhou: {proc.stderr.strip()}"
            return result

        # Avisos (ex: Syntax Warning: Invalid Font Weight) são ignorados.
        # Agora coletamos os arquivos gerados: page-1.jpg, page-2.jpg, ...
        raw_files = sorted(glob.glob(os.path.join(output_dir, "page-*.jpg")))

        pages = []
        for idx, fpath in enumerate(raw_files, start=1):
            new_name = f"page_{idx:02d}.jpg"
            new_path = os.path.join(output_dir, new_name)
            # Renomeia para padronizar o nome esperado pelo pipeline
            os.replace(fpath, new_path)
            pages.append(new_name)

        if not pages:
            result["error"] = "Nenhuma página convertida pelo pdftoppm"
            return result

        result["status"] = "success"
        result["pages"] = pages
        result["page_count"] = len(pages)
        return result

    except Exception as e:
        result["error"] = f"{e}\n{traceback.format_exc()}"
        return result