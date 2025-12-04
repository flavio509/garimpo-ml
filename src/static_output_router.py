from flask import send_file
from pathlib import Path

BASE_DIR = Path("/home/ubuntu/garimpo-ml/core_pipeline")
OUT_DIR  = BASE_DIR / "outputs"
DATA_DIR = BASE_DIR / "data"

def resolve_output_path(job_id: str, filename: str) -> Path:
    """
    Resolve qualquer arquivo relacionado ao JOB:
    - HTML final
    - crops
    - JPGs das páginas
    - JSONs
    """
    candidates = [
        OUT_DIR / job_id / filename,
        DATA_DIR / job_id / "outputs" / filename,
        DATA_DIR / job_id / "outputs" / "pages_jpg" / filename,
        DATA_DIR / job_id / "outputs" / "crops" / filename,
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def serve(job_id: str, filename: str):
    path = resolve_output_path(job_id, filename)
    if not path:
        return f"Arquivo não encontrado: {filename}", 404

    return send_file(str(path), conditional=True)