import shutil
from pathlib import Path

BASE = Path("/home/ubuntu/garimpo-ml/core_pipeline/data")

def cleanup(job_id: str):
    root = BASE / job_id / "outputs"
    dirs = ["ocr_json", "pages"]

    for d in dirs:
        p = root / d
        if p.exists():
            print(f"🗑️ Removendo {p}")
            shutil.rmtree(p, ignore_errors=True)

    print("🎯 Limpeza concluída.")

if __name__ == "__main__":
    import sys
    cleanup(sys.argv[1])
