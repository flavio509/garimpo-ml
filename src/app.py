from flask import Flask, render_template, request, redirect
from pathlib import Path
import subprocess
import datetime

app = Flask(__name__)

BASE_DIR = Path("/home/ubuntu/garimpo-ml")
DATA_DIR = BASE_DIR / "core_pipeline" / "data"
OUT_DIR  = BASE_DIR / "core_pipeline" / "outputs"


# --------------------------------------------------------
# Tela inicial de upload
# --------------------------------------------------------
@app.route("/upload/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # Aceita supplier OU supplier_name para manter compatibilidade
        supplier = request.form.get("supplier")
        if not supplier:
            supplier = request.form.get("supplier_name")

        file = request.files.get("file")

        if not supplier or not file:
            return "Fornecedor ou arquivo inválidos."

        supplier = supplier.strip().upper()
        date_tag = datetime.datetime.now().strftime("%Y%m%d")
        job_id = f"{supplier}_{date_tag}"

        job_dir = DATA_DIR / job_id / "uploads"
        job_dir.mkdir(parents=True, exist_ok=True)

        save_path = job_dir / "source.pdf"
        file.save(save_path)

        return redirect(
            f"/process/?supplier={supplier}&filename={save_path.name}&date_tag={date_tag}"
        )

    return render_template("upload.html")


# --------------------------------------------------------
# Tela que mostra os dados do upload
# --------------------------------------------------------
@app.route("/process/")
def process_view():
    supplier = request.args.get("supplier")
    filename = request.args.get("filename")
    date_tag = request.args.get("date_tag")

    job_id = f"{supplier}_{date_tag}"
    pdf_path = DATA_DIR / job_id / "uploads" / filename

    return render_template(
        "process.html",
        supplier=supplier,
        filename=filename,
        job_id=job_id,
        upload_path=str(pdf_path),  # nome usado no template
        date_tag=date_tag,
    )


# --------------------------------------------------------
# BOTÃO: "Iniciar processo de extração"
# Usa pipeline 2810 completo
# --------------------------------------------------------
@app.route("/process-run/<job_id>")
def process_run(job_id):
    # 1) Converter PDF → JPG
    cmd_convert = [
        "python3",
        "core_pipeline/converters/pdf_to_jpg_converter.py",
        job_id,
    ]
    subprocess.run(cmd_convert, cwd=str(BASE_DIR))

    # 2) OCR por página (modelo 2810)
    cmd_ocr = [
        "python3",
        "core_pipeline/extractors/ocr_page_processor.py",
        job_id,
    ]
    subprocess.run(cmd_ocr, cwd=str(BASE_DIR))

    # 3) Normalização
    cmd_norm = [
        "python3",
        "core_pipeline/pipeline_normalize_by_page.py",
        job_id,
    ]
    subprocess.run(cmd_norm, cwd=str(BASE_DIR))

    # 4) Consolidação final
    cmd_merge = [
        "python3",
        "core_pipeline/assembler/assemble_products.py",
        job_id,
    ]
    subprocess.run(cmd_merge, cwd=str(BASE_DIR))

    # 5) HTML interativo
    cmd_html = [
        "python3",
        "core_pipeline/assembler/generate_editable_html.py",
        job_id,
    ]
    subprocess.run(cmd_html, cwd=str(BASE_DIR))

    final_html = OUT_DIR / job_id / "catalogo_interativo.html"

    return f"""
        <h2>Processo finalizado!</h2>
        <p>Job: {job_id}</p>
        <p><a href="/static_output/{job_id}/catalogo_interativo.html" target="_blank">
            Abrir Catálogo Interativo
        </a></p>
        <p>Arquivo gerado: {final_html}</p>
    """


# --------------------------------------------------------
# Saída estática (HTML + JPG + crops + JSON)
# --------------------------------------------------------
from static_output_router import serve as serve_output

@app.route("/static_output/<job_id>/<path:filename>")
def static_output(job_id, filename):
    return serve_output(job_id, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)