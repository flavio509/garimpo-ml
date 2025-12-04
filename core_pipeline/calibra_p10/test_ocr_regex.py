import os, cv2
from utils_calibra import ocr_text, extract_from_text, second_pass_ocr

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
IMG_TPL = os.path.join(BASE, "data", "pages", "page_{:02}.jpg")

# Testar apenas páginas 4 a 6 (onde já vimos produtos antes)
for n in range(4, 7):
    path = IMG_TPL.format(n)
    if not os.path.exists(path):
        print(f"⚠️ Página {n} não encontrada: {path}")
        continue

    img = cv2.imread(path)
    h, w = img.shape[:2]
    # Cortar região central onde há produtos visuais
    crop = img[int(h*0.3):int(h*0.7), int(w*0.1):int(w*0.9)]

    txt1 = ocr_text(crop)
    txt2 = second_pass_ocr(crop)

    print(f"\n=== Página {n} ===")
    print("Primeira passada:")
    print(txt1[:500].replace("\n", " | "))
    print("\nSegunda passada:")
    print(txt2[:500].replace("\n", " | "))

    code1, price1 = extract_from_text(txt1)
    code2, price2 = extract_from_text(txt2)

    print(f"\nExtração 1: código={code1} | preço={price1}")
    print(f"Extração 2: código={code2} | preço={price2}")
