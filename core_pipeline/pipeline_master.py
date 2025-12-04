import subprocess, sys

scripts = [
    "core_pipeline/pipeline_convert_pdf.py",
    "core_pipeline/pipeline_detectron_ocr.py",
    "core_pipeline/pipeline_normalize_by_page.py",
    "core_pipeline/pipeline_generate_html_paginado.py",
]

for s in scripts:
    print(f"\n🧩 Executando {s} ...")
    subprocess.run([sys.executable, s], check=True)
print("\n🎯 Pipeline completo executado com sucesso.")
