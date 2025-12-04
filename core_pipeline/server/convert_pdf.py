import os, subprocess, json
from flask import Blueprint, request, jsonify
from datetime import datetime

convert_bp = Blueprint("convert_bp", __name__)

BASE_UPLOAD_DIR = os.path.join("data", "uploads")
PIPELINE_SCRIPTS = os.path.join("core_pipeline")

@convert_bp.route("/convert", methods=["POST"])
def convert_pdf():
    """
    Endpoint responsável por processar a conversão completa de um PDF previamente enviado.
    Ele utiliza o upload_id retornado no upload e executa a cadeia:
    PDF → Imagens → OCR → Normalização → HTML Paginado.
    """
    data = request.get_json(force=True)
    upload_id = data.get("upload_id")
    if not upload_id:
        return jsonify({"status": "error", "message": "upload_id ausente"}), 400

    upload_path = os.path.join(BASE_UPLOAD_DIR, upload_id)
    if not os.path.exists(upload_path):
        return jsonify({"status": "error", "message": f"Diretório não encontrado: {upload_id}"}), 404

    # Localiza o arquivo PDF
    pdf_files = [f for f in os.listdir(upload_path) if f.lower().endswith(".pdf")]
    if not pdf_files:
        return jsonify({"status": "error", "message": "Nenhum PDF encontrado"}), 404

    pdf_path = os.path.join(upload_path, pdf_files[0])
    result_log = []

    # 1️⃣ Conversão PDF → imagens
    try:
        subprocess.run([
            "python3",
            os.path.join(PIPELINE_SCRIPTS, "extractors/pdf_to_images.py"),
            pdf_path,
            os.path.join(upload_path, "pages")
        ], check=True)
        result_log.append("✅ Conversão PDF → imagens concluída")
    except subprocess.CalledProcessError as e:
        result_log.append(f"❌ Falha na conversão PDF → imagens: {e}")
        return jsonify({"status": "error", "log": result_log})

    # 2️⃣ OCR + extração de blocos
    try:
        subprocess.run([
            "python3",
            os.path.join(PIPELINE_SCRIPTS, "extractors/ocr_page_processor.py"),
            upload_path
        ], check=True)
        result_log.append("✅ OCR e extração de blocos concluídos")
    except subprocess.CalledProcessError as e:
        result_log.append(f"❌ Falha no OCR: {e}")
        return jsonify({"status": "error", "log": result_log})

    # 3️⃣ Normalização dos dados
    try:
        subprocess.run([
            "python3",
            os.path.join(PIPELINE_SCRIPTS, "normalizers/pipeline_normalize_by_page.py"),
            upload_path
        ], check=True)
        result_log.append("✅ Normalização concluída")
    except subprocess.CalledProcessError as e:
        result_log.append(f"❌ Falha na normalização: {e}")
        return jsonify({"status": "error", "log": result_log})

    # 4️⃣ Montagem de produtos e HTML paginado
    try:
        subprocess.run([
            "python3",
            os.path.join(PIPELINE_SCRIPTS, "assembler/generate_html_paginated.py"),
            upload_path
        ], check=True)
        result_log.append("✅ HTML paginado gerado com sucesso")
    except subprocess.CalledProcessError as e:
        result_log.append(f"❌ Falha ao gerar HTML: {e}")
        return jsonify({"status": "error", "log": result_log})

    # Caminho de saída final
    html_output = os.path.join(upload_path, "html", "catalogo_interativo.html")

    return jsonify({
        "status": "success",
        "message": "Conversão concluída com sucesso",
        "upload_id": upload_id,
        "html": html_output,
        "log": result_log
    })
