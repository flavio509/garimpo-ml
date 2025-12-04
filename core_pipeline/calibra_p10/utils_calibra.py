"""
Garimpo ML – Utilitários Calibra P10 (versão 2025-11-06)
---------------------------------------------------------
Atualizado para compatibilidade com o protocolo GarimpoML_Oficial_v1.
Funções de pré-processamento, OCR opcional e regex tolerante (código, título, preço).
"""

import cv2
import re
import numpy as np
import datetime
import os

# Caminho de log seguro
LOG_PATH = "/home/ubuntu/garimpo-ml/core_pipeline/outputs/calibra_p10_log.txt"

# ============================================================
# 1️⃣ Utilitários de log
# ============================================================
def log(msg: str):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now():%H:%M:%S}  {msg}\n")
    except Exception:
        pass


# ============================================================
# 2️⃣ Pré-processamento adaptativo
# ============================================================
def enhance_for_ocr(img, strong=False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    gray = cv2.convertScaleAbs(gray, alpha=1.4, beta=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        35,
        11,
    )
    return adaptive


# ============================================================
# 3️⃣ OCR duplo (habilitado apenas se pytesseract estiver ativo)
# ============================================================
def ocr_duplo(img, strong=False, enable_ocr=False):
    if not enable_ocr:
        return ""  # OCR desativado conforme protocolo

    import pytesseract

    if img is None or img.size == 0:
        return ""

    mean_val = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)) if len(img.shape) == 3 else np.mean(img)
    use_color_direct = mean_val > 210

    try:
        if use_color_direct:
            text = pytesseract.image_to_string(img, lang="por+eng", config="--psm 6")
        else:
            img_proc = enhance_for_ocr(img, strong=False)
            text = pytesseract.image_to_string(img_proc, lang="por+eng", config="--psm 7")
        text = text.strip()
    except Exception:
        text = ""

    if not text or len(text) < 3:
        try:
            img_proc2 = enhance_for_ocr(img, strong=True)
            text2 = pytesseract.image_to_string(img_proc2, lang="por+eng", config="--psm 6")
            return (text2 or "").strip()
        except Exception:
            return ""

    return text


# ============================================================
# 4️⃣ Localiza blocos de texto prováveis de produtos
# ============================================================
def find_boxes_multi(img):
    """
    Detecta blocos de produtos com robustez.
    Versão validada em 27/10 (funcionando para TABELA_TTBRASIL).
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1) Suavizar (reduce noise)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2) Threshold automático (Otsu) — muito mais robusto
    _, th = cv2.threshold(
        blur, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # 3) Dilatação horizontal – junta textos que pertencem ao mesmo bloco de produto
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 5))
    dil = cv2.dilate(th, kernel, iterations=2)

    # 4) Fecha pequenos buracos internos
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 7))
    closed = cv2.morphologyEx(dil, cv2.MORPH_CLOSE, close_kernel)

    # 5) Contornos
    cnts, _ = cv2.findContours(
        closed,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []
    H, W = gray.shape[:2]

    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)

        # 6) Filtros inteligentes da versão validada
        area = w * h
        if area < 8000:      # elimina lixo
            continue
        if w < 120 or h < 40:
            continue
        if w > W * 0.95:     # evita blocos enormes
            continue
        if h > H * 0.30:     # evita blocos verticais gigantes
            continue

        # Caixa final
        boxes.append((x, y, x + w, y + h, 1.0))

    # Ordenação top→bottom, left→right
    boxes.sort(key=lambda b: (b[1], b[0]))

    return boxes



# ============================================================
# 5️⃣ Divide regiões em linhas menores (casos densos)
# ============================================================
def split_lines(crop):
    h, w = crop.shape[:2]
    step = max(20, h // 20)
    return [(0, y, w, step) for y in range(0, h, step)]


# ============================================================
# 6️⃣ Extração regex pura de título, código e preço
# ============================================================
def extract_from_text(txt):
    raw = txt or ""
    txt = raw.replace("\n", " ").replace("|", " ").replace(":", " ").strip()
    txt = re.sub(r"\s{2,}", " ", txt)
    txt = txt.replace("R $", "R$").replace("RS", "R$")
    txt_upper = txt.upper()

    # --- Padrões regex robustos (corrigido e seguro) ---
    padrao = re.compile(
        r"(?P<codigo>[A-Z]{1,3}[- ]?\d{3,6})"                # captura código tipo CT2092
        r"[\s\-:]*"                                          # separadores opcionais
        r"(?P<titulo>[A-Z0-9Á-ÚÂÊÔÃÕÇa-z0-9 ,\-\°]{3,100})"  # título do produto
        r"[\s\-:]*"                                          # tolerância
        r"(?:R\$ ?(?P<preco>\d{1,3}(?:[\.,]\d{2})))",        # preço
        flags=re.IGNORECASE
    )

    produtos = []
    for match in padrao.finditer(txt):
        try:
            codigo = match.group("codigo").upper().replace(" ", "").replace("-", "")
            titulo = match.group("titulo") or ""
            titulo = re.sub(r"\bCT\d{3,6}\b", "", titulo)  # remove código duplicado
            titulo = titulo.strip().title()
            preco = match.group("preco") or ""
            preco_fmt = preco.replace(",", ".")
            preco_fmt = f"R$ {preco_fmt}"

            produtos.append({
                "titulo": titulo,
                "codigo": codigo,
                "preco": preco_fmt
            })

            # log detalhado
            path = "/home/ubuntu/garimpo-ml/core_pipeline/outputs/calibra_p10_log.txt"
            with open(path, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%H:%M:%S}  Código={codigo}, Preço={preco_fmt}, Título={titulo}\n")

        except Exception:
            continue

    # fallback: tenta capturar preços isolados
    if not produtos:
        codigos = re.findall(r"[A-Z]{1,3}[- ]?\d{3,6}", txt)
        precos = re.findall(r"(?:R\$ ?)?\d{1,3}(?:[\.,]\d{2})", txt)
        for c in codigos:
            preco = precos[0] if precos else ""
            preco_fmt = f"R$ {preco.replace(',', '.')}" if preco else ""
            produtos.append({
                "titulo": "(sem título)",
                "codigo": c,
                "preco": preco_fmt
            })

    return produtos


# ============================================================
# 7️⃣ Consolidação (remoção de duplicados)
# ============================================================
def consolidate_products(produtos_raw):
    if not produtos_raw:
        return []
    produtos_raw.sort(key=lambda p: p.get("codigo", ""))
    seen, unique = set(), []
    for pr in produtos_raw:
        key = f"{pr.get('codigo')}_{pr.get('preco')}"
        if key not in seen:
            seen.add(key)
            unique.append(pr)
    return unique

# ============================================================
# 8️⃣ Extrator UNIVERSAL (código, preço, título) — ordem flexível
#     Suporta padrões: (1) L+N, (2) L-hífen-N, (4) sufixos, (5) barras, (6) pontos
#     Ex.: CT2092 | AB-5560 | CT3021-P | PRO-200/5 | ABC.120
# ============================================================
import re

# preço: R$ 12,34 | R$12,34 | 12,34 (com ou sem símbolo, normalizamos com R$)
_RE_PRICE = re.compile(
    r"""(?P<price>
         (?:R\$\s*)?
         \d{1,3}
         (?:[.\s]?\d{3})*
         (?:[.,]\d{2})
        )""",
    re.VERBOSE
)

# códigos (família ampla)
# 1) Letras+Números (ex.: CT2092, A1234)
# 2) Letras-hífen-Números (ex.: AB-5560, CT-3021)
# 4) Sufixos opcionais (ex.: CT3021-P, A1020-2)
# 5) Barras (ex.: PRO-200/5)
# 6) Pontos (ex.: ABC.120)
_RE_CODE = re.compile(
    r"""(?P<code>
        [A-Z]{1,4}      # 1–4 letras iniciais
        (?:[-\.])?      # separador opcional (- ou .)
        \d{2,6}         # 2–6 dígitos
        (?:             # sufixos opcionais
           (?:[-/]\d{1,3}) |   # -2  ou /5
           (?:-[A-Z])    |     # -P
           (?:\.\d{1,3})       # .120
        )?
    )""",
    re.VERBOSE | re.IGNORECASE
)

def _norm_spaces(s: str) -> str:
    return re.sub(r"\s{2,}", " ", (s or "").replace("|", " ").replace(":", " ").strip())

def _norm_price(p: str) -> str:
    if not p:
        return ""
    p = p.replace(" ", "")
    p = p.replace("R$", "")
    p = p.replace(".", "")  # remove separador de milhar
    p = p.replace(",", ".") # padroniza decimal
    try:
        val = float(p)
        return f"R$ {val:.2f}".replace(".", ",")
    except Exception:
        # se já vier no formato correto, tenta preservar
        return f"R$ {p.replace('.', ',')}"

def find_code_candidates(txt: str):
    return list(_RE_CODE.finditer(txt))

def find_price_candidates(txt: str):
    return list(_RE_PRICE.finditer(txt))

def extract_from_text_universal(raw: str):
    """
    Extrai [{codigo, preco, titulo}] de um texto solto (ordem flexível).
    Estratégia:
      1) encontra todos os códigos e preços (com spans)
      2) cria pares código↔preço pela proximidade no texto
      3) o título é o trecho "entre" (ou ao redor) do par
      4) normaliza e remove repetições
    Retorna lista (pode vir vazia). Não levanta exceção.
    """
    txt = _norm_spaces(raw or "")
    if not txt:
        return []

    code_matches = find_code_candidates(txt)
    price_matches = find_price_candidates(txt)

    # se não encontrar preço com símbolo, tenta capturar 12,34 “solto”
    if not price_matches:
        price_matches = list(re.finditer(r"\d{1,3}(?:[.\s]?\d{3})*(?:[.,]\d{2})", txt))

    results = []
    used_keys = set()

    # associa cada código ao preço mais próximo (janela local)
    for cm in code_matches:
        c_span = cm.span()
        c_text = cm.group("code").upper().replace(" ", "")
        c_start, c_end = c_span

        # escolhe o preço mais próximo do código
        nearest = None
        nearest_dist = 10**9
        for pm in price_matches:
            p_span = pm.span()
            dist = min(abs(p_span[0] - c_end), abs(p_span[1] - c_start))
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = pm

        # monta registro
        if nearest:
            p_text_raw = nearest.group(0)
            price_norm = _norm_price(p_text_raw)

            # título = trecho entre código e preço (ou ao redor, se invertido)
            s1, e1 = c_span
            s2, e2 = nearest.span()
            left, right = (e1, s2) if e1 <= s2 else (e2, s1)
            title_candidate = txt[left:right].strip()

            # fallback se vazio: pega 40 chars ao redor do código
            if len(title_candidate) < 3:
                start = max(0, s1 - 40)
                end = min(len(txt), e1 + 40)
                title_candidate = txt[start:end].strip()

            # limpa título de duplicatas óbvias
            title_clean = re.sub(r"\b" + re.escape(c_text) + r"\b", "", title_candidate, flags=re.IGNORECASE)
            title_clean = re.sub(r"\bR\$\s*\d+[.,]\d{2}\b", "", title_clean, flags=re.IGNORECASE)
            title_clean = _norm_spaces(title_clean).strip().strip("-–,.;")

            key = (c_text, price_norm, title_clean[:40].lower())
            if key in used_keys:
                continue
            used_keys.add(key)

            results.append({
                "codigo": c_text,
                "preco": price_norm,
                "titulo": title_clean if title_clean else "(sem título)"
            })

    # dedup por código+preço; preserva o primeiro título não vazio
    unique = {}
    for r in results:
        k = (r["codigo"], r["preco"])
        if k not in unique or (unique[k]["titulo"] == "(sem título)" and r["titulo"] != "(sem título)"):
            unique[k] = r

    return list(unique.values())
