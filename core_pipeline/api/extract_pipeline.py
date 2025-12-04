import os
import sys
import json
import traceback
import subprocess
import shutil
from pathlib import Path

# =========================================================
# 🔹 Garantir que o pacote core_pipeline seja importável
#    quando o script é chamado via caminho absoluto
# =========================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core_pipeline.api.pdf_to_jpg_converter import convert_pdf_to_jpg
from core_pipeline.api.ocr_page_processor import run_ocr, _group_tokens_by_y, _concat_line_tokens


# =========================================================
# 🔹 Configurações fixas de caminhos
# =========================================================
DATA_ROOT = "/home/ubuntu/garimpo-ml/core_pipeline/data"
CENTRAL_OUTPUT_ROOT = "/home/ubuntu/garimpo-ml/core_pipeline/outputs"
PYTHON_BIN = "/home/ubuntu/garimpo-ml/venv/bin/python3"


# =========================================================
# 🔹 Utilitários
# =========================================================
def ensure_dir(path: str | Path):
    Path(path).mkdir(parents=True, exist_ok=True)


def write_progress(progress_path: Path, status: str, progress: int, step: str):
    data = {
        "status": status,
        "progress": progress,
        "step": step
    }
    try:
        with progress_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # Não derruba o pipeline se falhar ao escrever progresso
        pass


# =========================================================
# 🔹 Etapas do pipeline
# =========================================================
def step_convert_pdf_to_jpg(pdf_path: Path, pages_dir: Path):
    """
    Etapa 1: PDF → JPG usando pdf_to_jpg_converter.py
    """
    ensure_dir(pages_dir)
    conv = convert_pdf_to_jpg(str(pdf_path), str(pages_dir))
    return conv


def step_ocr_pages(pages_dir: Path, ocr_dir: Path):
    """
    Etapa 2: OCR de cada página.
    Usa run_ocr + agrupamento visual para gerar uma lista de linhas de texto.
    Salva arquivos:
        ocr_dir/page_XX_ocr.json  (lista de strings)
    Retorna lista de páginas processadas.
    """
    ensure_dir(ocr_dir)

    page_files = sorted(
        [p for p in pages_dir.iterdir() if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png"]],
        key=lambda p: p.name
    )

    processed_pages = []

    for idx, img_path in enumerate(page_files, start=1):
        ocr_res = run_ocr(str(img_path))
        if ocr_res.get("status") != "success":
            # Se falhar, apenas registra e segue
            continue

        tokens = ocr_res.get("tokens", [])
        linhas = _group_tokens_by_y(tokens, max_gap=25)
        linhas_concat = _concat_line_tokens(linhas)

        page_num = idx  # assume ordenação natural da conversão
        out_json = ocr_dir / f"page_{page_num:02d}_ocr.json"

        with out_json.open("w", encoding="utf-8") as f:
            json.dump(linhas_concat, f, ensure_ascii=False, indent=2)

        processed_pages.append(page_num)

    return processed_pages


def step_copy_ocr_to_central(ocr_dir: Path, central_job_dir: Path):
    """
    Copia os arquivos page_XX_ocr.json do job para:
        core_pipeline/outputs/<JOB_ID>/
    que é onde pipeline_normalize_by_page.py espera encontrar.
    """
    ensure_dir(central_job_dir)

    for src in sorted(ocr_dir.glob("page_*_ocr.json")):
        dst = central_job_dir / src.name
        shutil.copyfile(src, dst)


def step_run_normalize(job_id: str, cwd: str):
    """
    Etapa 3: chama pipeline_normalize_by_page.py via subprocess.
    """
    cmd = [PYTHON_BIN, "core_pipeline/pipeline_normalize_by_page.py", job_id]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Falha na normalização.\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )


def step_run_assemble(job_id: str, cwd: str):
    """
    Etapa 4: chama assemble_products.py via subprocess.
    """
    cmd = [PYTHON_BIN, "core_pipeline/assemble_products.py", job_id]
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Falha no assemble.\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}"
        )


def step_generate_job_catalog(job_id: str, supplier: str, date_tag: str, job_outputs_dir: Path):
    """
    Etapa 5: lê core_pipeline/outputs/<JOB_ID>/catalogo_base.json
    e grava dentro do job:
        <job_outputs_dir>/catalog_raw.json
    no formato esperado pelo HTML (dict com 'products').
    """
    central_job_dir = Path(CENTRAL_OUTPUT_ROOT) / job_id
    catalog_central = central_job_dir / "catalogo_base.json"

    if not catalog_central.exists():
        raise FileNotFoundError(f"catalogo_base.json não encontrado em {catalog_central}")

    with catalog_central.open("r", encoding="utf-8") as f:
        produtos = json.load(f)

    if not isinstance(produtos, list):
        raise ValueError("catalogo_base.json inválido: esperado list de produtos.")

    ensure_dir(job_outputs_dir)
    catalog_job = job_outputs_dir / "catalog_raw.json"

    payload = {
        "job_id": job_id,
        "supplier": supplier,
        "date_tag": date_tag,
        "products_count": len(produtos),
        "products": produtos
    }

    with catalog_job.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return str(catalog_job)


# =========================================================
# 🔹 Função principal de orquestração
# =========================================================
def run_extract_for_job(supplier: str, date_tag: str) -> dict:
    """
    Orquestra o pipeline completo para um JOB:
        PDF → JPG → OCR → NORMALIZE → ASSEMBLE → catalog_raw.json
    """
    job_id = f"{supplier}_{date_tag}"

    job_dir = Path(DATA_ROOT) / job_id
    uploads_dir = job_dir / "uploads"
    outputs_dir = job_dir / "outputs"
    pages_dir = outputs_dir / "pages_jpg"
    ocr_dir = outputs_dir / "ocr_json"
    progress_path = job_dir / "progress.json"

    ensure_dir(uploads_dir)
    ensure_dir(outputs_dir)

    pdf_path = uploads_dir / "source.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF não encontrado em {pdf_path}")

    result = {
        "status": "error",
        "job_id": job_id,
        "pdf_path": str(pdf_path),
        "outputs_dir": str(outputs_dir),
        "catalog_json": None,
        "error": None,
        "traceback": None
    }

    # Registrar início
    write_progress(progress_path, "Iniciando extração", 1, "start")

    try:
        # ------------------------------
        # 1) PDF → JPG
        # ------------------------------
        write_progress(progress_path, "Convertendo PDF em imagens", 5, "pdf_to_jpg")
        conv = step_convert_pdf_to_jpg(pdf_path, pages_dir)
        if conv.get("status") != "success":
            err = conv.get("error") or "Falha na conversão PDF→JPG (sem detalhe)."
            write_progress(progress_path, f"Erro na conversão: {err}", 100, "error_pdf_to_jpg")
            result["error"] = err
            return result

        # ------------------------------
        # 2) OCR páginas
        # ------------------------------
        write_progress(progress_path, "Executando OCR nas páginas", 20, "ocr_pages")
        processed_pages = step_ocr_pages(pages_dir, ocr_dir)
        if not processed_pages:
            msg = "Nenhuma página processada no OCR."
            write_progress(progress_path, msg, 100, "error_ocr")
            result["error"] = msg
            return result

        # ------------------------------
        # 3) Copiar OCR para workspace central
        # ------------------------------
        central_job_dir = Path(CENTRAL_OUTPUT_ROOT) / job_id
        write_progress(progress_path, "Copiando OCR para workspace central", 35, "copy_ocr")
        step_copy_ocr_to_central(ocr_dir, central_job_dir)

        # ------------------------------
        # 4) Normalizar páginas (subprocesso)
        # ------------------------------
        write_progress(progress_path, "Normalizando páginas", 55, "normalize_pages")
        step_run_normalize(job_id, cwd="/home/ubuntu/garimpo-ml")

        # ------------------------------
        # 5) Assemble de produtos (subprocesso)
        # ------------------------------
        write_progress(progress_path, "Montando catálogo final", 75, "assemble_catalog")
        step_run_assemble(job_id, cwd="/home/ubuntu/garimpo-ml")

        # ------------------------------
        # 6) Gerar catalog_raw.json dentro do job
        # ------------------------------
        write_progress(progress_path, "Gerando catalog_raw.json do job", 90, "job_catalog")
        catalog_path = step_generate_job_catalog(job_id, supplier, date_tag, outputs_dir)

        # ------------------------------
        # 7) Finalização
        # ------------------------------
        write_progress(progress_path, "Extração finalizada", 100, "done")

        result["status"] = "success"
        result["catalog_json"] = catalog_path
        return result

    except Exception as e:
        tb = traceback.format_exc()
        write_progress(progress_path, f"Erro fatal: {str(e)}", 100, "fatal")
        result["error"] = str(e)
        result["traceback"] = tb
        return result


# =========================================================
# 🔹 Runner principal quando chamado via subprocess
# =========================================================
if __name__ == "__main__":
    supplier = os.environ.get("SUPPLIER_NAME")
    date_tag = os.environ.get("SUPPLIER_DATE")

    if not supplier or not date_tag:
        raise SystemExit("Variáveis SUPPLIER_NAME e SUPPLIER_DATE não foram definidas.")

    supplier = supplier.strip().upper()
    date_tag = date_tag.strip()

    res = run_extract_for_job(supplier, date_tag)
    if res.get("status") != "success":
        # Garante que o processo retorna código != 0 em caso de erro
        print(f"[ERROR] {res.get('error')}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"[OK] Extração concluída. Catálogo em: {res.get('catalog_json')}")
