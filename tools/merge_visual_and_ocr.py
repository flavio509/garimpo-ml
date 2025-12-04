#!/usr/bin/env python3
import json, sys, re
from pathlib import Path

if len(sys.argv) < 3:
    print("Uso: python tools/merge_visual_and_ocr.py out/ttbrasil_visual.json out/ocr_normalized.json")
    sys.exit(1)

vis = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
ocr = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

def pick(d,k):
    return d.get(k) or d.get(k.capitalize()) or ""

def keycode(s:str)->str:
    s = (s or "").upper()
    m = re.search(r"\bCT\d{3,6}\b", s)
    return m.group(0) if m else s.strip()

by = {}

# prioridade 1: visual_cluster (tem imagem boa e preço coerente)
for it in vis:
    code = keycode(pick(it,"code") or pick(it,"codigo"))
    if not code: continue
    by[code] = {
        "image": pick(it,"image"),
        "code":  code,
        "title": pick(it,"title") or pick(it,"titulo"),
        "price": pick(it,"price") or pick(it,"preco"),
        "source": "visual"
    }

# prioridade 2: OCR (só preenche se não existir, ou para completar campos vazios)
for it in ocr:
    code = keycode(pick(it,"code") or pick(it,"codigo") or pick(it,"title"))
    if not code: continue
    cur = by.get(code, {"image":"", "code":code, "title":"", "price":"","source":"ocr"})
    # completa só se vazio
    cur["title"] = cur["title"] or pick(it,"title") or pick(it,"titulo")
    cur["price"] = cur["price"] or pick(it,"price") or pick(it,"preco")
    cur["image"] = cur["image"] or pick(it,"image") or pick(it,"thumb")
    by[code] = cur

merged = list(by.values())
Path("out/merged_catalog.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[✔] Mesclados: {len(merged)} → out/merged_catalog.json")

# reaproveita o renderer acima (inline simples):
html = Path("out/catalogo_ttbrasil_interativo_linhas.html")
from html import escape as esc
rows = merged
doc = ["<!doctype html><meta charset='utf-8'><title>Catálogo (mesclado)</title>",
"<style>body{font-family:Arial,sans-serif;background:#f7f7fb}table{width:100%;max-width:1280px;margin:20px auto;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,.06)}th,td{border-bottom:1px solid #eee;padding:10px 12px}th{background:#f0f3f9}</style>",
"<table><thead><tr><th>Imagem</th><th>Código</th><th>Título</th><th>Preço</th><th>Fonte</th></tr></thead><tbody>"]
for r in rows:
    img = esc(r.get("image",""))
    code= esc(r.get("code",""))
    title=esc(r.get("title",""))
    price=esc(r.get("price",""))
    src = esc(r.get("source",""))
    imgc = f"<img src='{img}' style='max-width:88px;max-height:88px'>" if img else "-"
    doc += [f"<tr><td>{imgc}</td><td>{code}</td><td>{title}</td><td>{price}</td><td>{src}</td></tr>"]
doc += ["</tbody></table>"]
html.write_text("\n".join(doc), encoding="utf-8")
print(f"[✔] HTML mesclado: {html}")
