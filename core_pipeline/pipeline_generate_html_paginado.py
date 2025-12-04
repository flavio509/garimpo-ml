import json, re
from pathlib import Path

OUT_DIR = Path("core_pipeline/outputs")
norm_files = sorted(OUT_DIR.glob("normalized_page_*.json"), key=lambda p: int(re.findall(r'\d+', p.stem)[0]))

sections, nav_links = [], []

for nf in norm_files:
    pg = int(re.findall(r'\d+', nf.stem)[0])
    produtos = json.load(open(nf, "r", encoding="utf-8"))
    cards = []
    for p in produtos:
        cards.append(f"""
        <div class='card'>
            <div class='codigo'>{p.get("codigo","—")}</div>
            <div class='titulo'>{p.get("titulo","")}</div>
            <div class='preco'>{p.get("preco","—")}</div>
        </div>""")
    sections.append(f"<section id='page_{pg}' class='page-section'>{''.join(cards)}</section>")
    nav_links.append(f"<a href='#page_{pg}'>Página {pg}</a>")

html = f"""
<!DOCTYPE html><html lang='pt-br'><head><meta charset='UTF-8'>
<title>Catálogo TTBRASIL - Paginado</title>
<style>
body{{font-family:Arial,sans-serif;background:#fafafa;margin:0}}
.page-section{{display:none;padding:15px}}
.page-section.active{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}}
.card{{background:#fff;border-radius:10px;padding:10px;box-shadow:0 1px 4px rgba(0,0,0,0.1)}}
.card .codigo{{color:#003366;font-weight:bold}}
.card .preco{{color:green;font-weight:bold}}
nav{{background:#eee;text-align:center;padding:10px;position:sticky;bottom:0}}
nav a{{margin:0 5px;color:#003366;text-decoration:none}}
</style></head><body>
<h1>Catálogo TTBRASIL – Revisão Paginada</h1>
{''.join(sections)}
<nav>{' | '.join(nav_links)}</nav>
<script>
const pages=document.querySelectorAll('.page-section');
function show(n){{pages.forEach(p=>p.classList.remove('active'));document.getElementById('page_'+n).classList.add('active');}}
document.querySelectorAll('nav a').forEach(a=>a.onclick=e=>{{e.preventDefault();show(e.target.textContent.match(/\\d+/)[0]);}});
show(1);
</script></body></html>
"""

html_path = OUT_DIR / "catalogo_ttbrasil_paginado.html"
html_path.write_text(html, encoding="utf-8")
print(f"✅ Catálogo HTML paginado gerado: {html_path}")
