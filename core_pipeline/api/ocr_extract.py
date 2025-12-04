import os
import json
import time
import subprocess
from paddleocr import PaddleOCR

def update_progress_file(progress_file, supplier, status, progress, step):
    data = {
        "supplier": supplier,
        "status": status,
        "progress": progress,
        "step": step,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(progress_file, "w") as f:
        json.dump(data, f, indent=2)

def normalize_paddleocr_output(raw_ocr):
    blocks = []
    for line_group in raw_ocr:
        for line in line_group:
            bbox = line[0]
            text = line[1][0]
            blocks.append({"text": text, "bbox": bbox})
    return {"blocks": blocks}

def _pdftoppm_image(pdf_path, page_number, output_path):
    """
    Gera imagem JPG usando o pdftoppm (100% compatível com Poppler).
    """
    cmd = [
        "pdftoppm",
        "-jpeg",
        "-r", "200",
        "-f", str(page_number),
        "-l", str(page_number),
        pdf_path,
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    final = f"{output_path}-{page_number}.jpg"
    return final

def run_ocr_pages(pdf_path, output_dir, progress_file, supplier):
    """
    Agora totalmente baseado em Poppler → SEM FITZ.
    """

    # Obtém número de páginas REAL via pdfinfo
    info_cmd = ["pdfinfo", pdf_path]
    raw = subprocess.check_output(info_cmd).decode("utf-8")
    total_pages = 0
    for line in raw.split("\n"):
        if line.startswith("Pages:"):
            total_pages = int(line.split(":")[1].strip())
            break

    update_progress_file(progress_file, supplier, "running", 5,
                         f"OCR iniciado ({total_pages} páginas)")

    os.makedirs(output_dir, exist_ok=True)
    ocr = PaddleOCR(use_angle_cls=True, lang="pt", show_log=False)

    for i in range(1, total_pages + 1):
        step_desc = f"OCR página {i}/{total_pages}"

        # --- Renderizar imagem com Poppler ---
        raw_img = os.path.join(output_dir, "render")
        img_path = _pdftoppm_image(pdf_path, i, raw_img)

        # --- OCR ---
        raw_result = ocr.ocr(img_path, cls=True)
        normalized = normalize_paddleocr_output(raw_result)

        # --- Salvar JSON ---
        json_path = os.path.join(output_dir, f"ocr_page_{i:02d}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(normalized, jf, ensure_ascii=False, indent=2)

        progress = int((i / total_pages) * 100)
        update_progress_file(progress_file, supplier, "running", progress, step_desc)

    update_progress_file(progress_file, supplier, "done", 100,
                         "OCR concluído com sucesso")

    return total_pages
