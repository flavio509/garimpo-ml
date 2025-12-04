
from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime
import os, uuid, re

upload_bp = Blueprint("upload_bp", __name__)

def _find_root(start: Path) -> Path:
    p = start.resolve()
    for parent in [p] + list(p.parents):
        if (parent / "data").exists():
            return parent
    return p.parents[2]

HERE = Path(__file__).resolve().parent
ROOT_DIR = _find_root(HERE)
BASE_UPLOAD_DIR = ROOT_DIR / "data" / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _slugify_supplier(s: str) -> str:
    s = (s or "FORNECEDOR").strip().upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "FORNECEDOR"

def _new_upload_id(fornecedor: str) -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    rnd = uuid.uuid4().hex[:6]
    return f"{ts}_{_slugify_supplier(fornecedor)}_{rnd}"

def _prepare_dirs(upload_id: str):
    base = BASE_UPLOAD_DIR / upload_id
    d = {
        "base": base,
        "source": base / "source",
        "pages": base / "pages",
        "outputs": base / "outputs",
        "html": base / "html",
    }
    for v in d.values():
        v.mkdir(parents=True, exist_ok=True)
    return d

def _is_pdf_filename(name: str) -> bool:
    return name.lower().endswith(".pdf")

@upload_bp.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file") or request.files.get("pdf")
    if not file or not getattr(file, "filename", ""):
        return jsonify({"status": "error", "message": "Nenhum arquivo enviado"}), 400
    if not _is_pdf_filename(file.filename):
        return jsonify({"status": "error", "message": "Apenas PDF é aceito (.pdf)"}), 400

    fornecedor = request.form.get("fornecedor") or request.form.get("supplier") or "FORNECEDOR"
    usuario = request.form.get("usuario", "anonimo")

    upload_id = _new_upload_id(fornecedor)
    dirs = _prepare_dirs(upload_id)

    pdf_path = dirs["source"] / "source.pdf"
    file.save(pdf_path.as_posix())

    manifest = dirs["base"] / "manifest.txt"
    manifest.write_text(
        f"upload_id: {upload_id}\n"
        f"fornecedor: {fornecedor}\n"
        f"usuario: {usuario}\n"
        f"original_filename: {file.filename}\n"
        f"saved_as: {pdf_path}\n"
        f"created_at: {datetime.now().isoformat()}\n",
        encoding="utf-8",
    )

    return jsonify({
        "status": "success",
        "upload_id": upload_id,
        "fornecedor": _slugify_supplier(fornecedor),
        "usuario": usuario,
        "paths": {
            "base": str(dirs["base"]),
            "source_pdf": str(pdf_path),
            "pages": str(dirs["pages"]),
            "outputs": str(dirs["outputs"]),
            "html": str(dirs["html"]),
        }
    }), 201
