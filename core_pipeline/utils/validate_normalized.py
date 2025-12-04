"""
Garimpo ML - Validador de Consistência dos JSONs Normalizados
Verifica se cada produto extraído possui campos essenciais:
codigo, titulo, preco e imagem.
Gera relatório técnico em CSV e log detalhado.
"""

import os
import json
import csv
from datetime import datetime

BASE_DIR = "/home/ubuntu/garimpo-ml"
OUTPUT_DIR = os.path.join(BASE_DIR, "core_pipeline", "outputs")
REPORT_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(REPORT_DIR, exist_ok=True)

LOG_PATH = os.path.join(REPORT_DIR, "validate_normalized.log")
CSV_REPORT = os.path.join(REPORT_DIR, "normalized_validation_report.csv")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def validate_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    issues = []
    valid_count = 0

    for idx, produto in enumerate(data):
        missing = []
        for field in ["codigo", "titulo", "preco", "imagem"]:
            if field not in produto or not str(produto[field]).strip():
                missing.append(field)
        if missing:
            issues.append({
                "arquivo": os.path.basename(file_path),
                "produto_idx": idx + 1,
                "faltando": ", ".join(missing)
            })
        else:
            valid_count += 1

    return valid_count, issues

def main():
    log("==== INÍCIO validação dos JSONs normalizados ====")
    all_issues = []
    total_valid = 0
    total_produtos = 0

    files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.startswith("normalized_page_") and f.endswith(".json")])
    for f_json in files:
        file_path = os.path.join(OUTPUT_DIR, f_json)
        valid, issues = validate_json(file_path)
        total_valid += valid
        total_produtos += valid + len(issues)
        all_issues.extend(issues)
        log(f"[{f_json}] {valid} válidos, {len(issues)} com problemas")

    # salvar CSV
    with open(CSV_REPORT, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["arquivo", "produto_idx", "faltando"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for issue in all_issues:
            writer.writerow(issue)

    log(f"Total de produtos válidos: {total_valid}")
    log(f"Total de produtos com problema: {len(all_issues)}")
    log(f"Relatório salvo em {CSV_REPORT}")
    log("==== FIM validação ====")

if __name__ == "__main__":
    main()
