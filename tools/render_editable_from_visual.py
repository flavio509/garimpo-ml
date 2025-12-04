#!/usr/bin/env python3
import json, sys
from pathlib import Path
from html import escape as esc

if len(sys.argv) < 2:
    print("Uso: python tools/render_editable_from_visual.py out/ttbrasil_visual.json")
    sys.exit(1)

src = Path(sys.argv[1])
data = json.loads(src.read_text(encoding="utf-8"))
out_html = Path("out/catalogo_ttbrasil_interativo_linhas.html")

def val(d,k):
    return d.get(k) or d.get(k.capitalize()) or ""

rows = []
for it in data:
    rows.append({
        "image": val(it,"image"),
        "code":  val(it,"code") or val(it,"codigo"),
        "title": val(it,"title") or val(it,"titulo"),
        "price": val(it,"price") or val(it,"preco"),
    })

html = []
html += [
"<!doctype html><html lang='pt-br'><head><meta charset='utf-8'>",
"<title>Catálogo Interativo (linhas)</title>",
"<style>",
"body{font-family:system-ui,Arial,sans-serif;background:#f7f7fb;margin:0}",
"header{display:flex;gap:12px;align-items:center;padding:16px 24px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.08)}",
"h1{font-size:20px;margin:0}",
".btn{background:#2563eb;color:#fff;border:none;border-radius:8px;padding:10px 14px;cursor:pointer}",
".search{flex:1;max-width:520px;padding:10px 12px;border:1px solid #ddd;border-radius:8px}",
"table{width:100%;border-collapse:collapse;background:#fff;margin:18px auto;max-width:1280px;border-radius:12px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,.06)}",
"th,td{border-bottom:1px solid #eee;padding:10px 12px;text-align:left;vertical-align:middle}",
"th{background:#f0f3f9;font-weight:600}",
"tr:hover{background:#fafcff}",
"input[type=text]{width:100%;padding:8px 10px;border:1px solid #dce1ee;border-radius:8px}",
".imgwrap{width:88px;height:88px;display:flex;align-items:center;justify-content:center;background:#fafafa;border:1px solid #eee;border-radius:10px;overflow:hidden}",
".imgwrap img{max-width:100%;max-height:100%;display:block}",
".muted{color:#6b7280;font-size:12px}",
"</style>",
"<script>",
"function salvar(){",
"  const rows=[...document.querySelectorAll('tbody tr')];",
"  const out=rows.map(tr=>({",
"    image: tr.querySelector('.col-img').dataset.src || '',",
"    code: tr.querySelector('.col-code').value.trim(),",
"    title: tr.querySelector('.col-title').value.trim(),",
"    price: tr.querySelector('.col-price').value.trim()",
"  }));",
"  const blob=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});",
"  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);",
"  a.download='catalogo_editado.json'; a.click();",
"}",
"function filtrar(v){v=v.toLowerCase();document.querySelectorAll('tbody tr').forEach(tr=>{const t=tr.innerText.toLowerCase();tr.style.display=t.includes(v)?'':'none';});}",
"</script>",
"</head><body>",
"<header>",
"<h1>📄 Catálogo Interativo (linhas)</h1>",
"<input class='search' placeholder='Buscar por código, título ou preço...' oninput='filtrar(this.value)'>",
"<button class='btn' onclick='salvar()'>💾 Salvar alterações</button>",
"</header>",
"<main><table>",
"<thead><tr><th>Imagem</th><th>Código</th><th>Título</th><th>Preço</th></tr></thead><tbody>"
]

for r in rows:
    img = esc(r["image"])
    code = esc(r["code"])
    title= esc(r["title"])
    price= esc(r["price"])
    img_cell = f"<div class='imgwrap col-img' data-src='{img}'>" + (f"<img src='{img}'>" if img else "<span class='muted'>sem imagem</span>") + "</div>"
    html += [
        "<tr>",
        f"<td>{img_cell}</td>",
        f"<td><input class='col-code' type='text' value='{code}'></td>",
        f"<td><input class='col-title' type='text' value='{title}'></td>",
        f"<td><input class='col-price' type='text' value='{price}'></td>",
        "</tr>"
    ]

html += ["</tbody></table></main></body></html>"]
out_html.write_text("\n".join(html), encoding="utf-8")
print(f"[✔] HTML (linhas) gerado: {out_html}")
