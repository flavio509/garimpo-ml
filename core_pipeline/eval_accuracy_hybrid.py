import csv, os

fast_path = "core_pipeline/outputs/p10_summary_fast.csv"
paddle_path = "core_pipeline/outputs/p10_summary_paddle.csv"

# === Tabela manual de referência ===
manual_counts = {
    1: 0, 2: 0, 3: 0,
    4: 6, 5: 5, 6: 3,
    7: 7, 8: 6, 9: 6,
    10: 0
}

def load_csv(path):
    data = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                page = int(row['pagina'])
                prod = int(row.get('produtos_detectados', 0))
                data[page] = prod
            except Exception:
                continue
    return data

# === Carregar resultados ===
fast_data = load_csv(fast_path)
paddle_data = load_csv(paddle_path)

# === Combinação: prioriza Paddle se detectou algo ===
hybrid = {}
for p in range(1, 11):
    val_paddle = paddle_data.get(p, 0)
    val_fast = fast_data.get(p, 0)
    hybrid[p] = val_paddle if val_paddle > 0 else val_fast

# === Avaliação ===
print("Pág.  Fast  Paddle  Escolhido  Manual  Dif  Precisão (%)")
print("-----------------------------------------------------------")

total_ocr = total_manual = 0
for i in range(1, 11):
    f = fast_data.get(i, 0)
    pa = paddle_data.get(i, 0)
    h = hybrid[i]
    m = manual_counts[i]
    diff = abs(h - m)
    prec = (1 - diff / m) * 100 if m else 0
    total_ocr += h
    total_manual += m
    print(f"{i:<6}{f:<6}{pa:<8}{h:<10}{m:<8}{diff:<4}{prec:<10.1f}")

prec_total = (total_ocr / total_manual) * 100 if total_manual else 0
print("-----------------------------------------------------------")
print(f"{'Total':<6}{'':<6}{'':<8}{total_ocr:<10}{total_manual:<8}{'':<4}{prec_total:<10.1f}")

# === Salvar saída ===
out_path = "core_pipeline/outputs/p10_accuracy_hybrid.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(f"Híbrido total: OCR={total_ocr}, Manual={total_manual}, Precisão={prec_total:.1f}%\n")
print(f"\n📄 Resultado salvo em: {os.path.abspath(out_path)}")
