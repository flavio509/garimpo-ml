import os
import json
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path("/home/ubuntu/garimpo-ml/core_pipeline")
OUTPUT_DIR = BASE_DIR / "outputs"


def generate_html(upload_id: str) -> None:
    base_dir = OUTPUT_DIR / upload_id if upload_id else OUTPUT_DIR
    input_json = base_dir / "catalogo_base.json"
    out_html = base_dir / "catalogo_interativo.html"

    if not input_json.exists():
        print(f"❌ Arquivo {input_json} não encontrado.")
        return

    with input_json.open("r", encoding="utf-8") as f:
        produtos = json.load(f)

    pages = defaultdict(list)
    for p in produtos:
        pg = int(p.get("page", 0) or 0)
        if pg <= 0:
            continue
        pages[pg].append(p)

    pages_data = {pg: items for pg, items in sorted(pages.items())}
    pages_json = json.dumps(pages_data, ensure_ascii=False, indent=2)

    html = f"""<!DOCTYPE html>
<html lang='pt-br'>
<head>
<meta charset='utf-8'>
<title>Catálogo Interativo (linha a linha)</title>
<style>
body{{font-family:Arial, sans-serif;background:#f5f5f5;margin:0;padding:0;}}
header{{background:#222;color:#fff;padding:12px 20px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}}
h1{{margin:0;font-size:22px;}}
button{{padding:6px 12px;margin:4px;border:none;border-radius:4px;color:#fff;cursor:pointer;font-weight:bold;}}
.btn-add{{background:#007bff;}} .btn-add:hover{{background:#0069d9;}}
.btn-export{{background:#28a745;}} .btn-export:hover{{background:#218838;}}
.btn-remove{{background:#dc3545;}} .btn-remove:hover{{background:#bb2d3b;}}
.btn-save{{background:#17a2b8;}} .btn-save:hover{{background:#138496;}}
.btn-save-all{{background:#6f42c1;}} .btn-save-all:hover{{background:#5936a2;}}
.pagination{{text-align:center;margin:20px;}}
table{{width:98%;margin:10px auto;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;}}
th,td{{padding:8px;border-bottom:1px solid #ddd;text-align:left;font-size:14px;}}
th{{background:#f8f9fa;}}
img{{max-height:80px;object-fit:contain;border:1px solid #ccc;border-radius:6px;background:#fff;}}
input[type=text],textarea{{width:100%;border:1px solid #ccc;border-radius:4px;padding:6px;font-size:14px;}}
#msg{{color:#00ff88;font-weight:bold;margin-left:10px;}}
</style>
</head>
<body>
<header>
<h1>📘 Catálogo Interativo ({upload_id})</h1>
<button class='btn-add' onclick='addProduto()'>+ Adicionar</button>
<button class='btn-save-all' onclick='saveAll()'>💾 Salvar todas</button>
<button class='btn-export' onclick='exportJSON()'>📤 Exportar JSON</button>
<span id="msg"></span>
</header>

<div class='pagination' id='pagination'></div>

<table id='tbl'>
<thead>
<tr>
  <th>Imagem</th>
  <th>Código</th>
  <th>Título</th>
  <th>Preço</th>
  <th>Ações</th>
</tr>
</thead>
<tbody id='tbody'></tbody>
</table>

<script>
const PAGES_DATA = {pages_json};
let currentPage = 1;

function loadPage(page){{
  currentPage = page;
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';
  const produtos = PAGES_DATA[page] || [];
  produtos.forEach((p,i) => {{
    const tr = document.createElement('tr');

    const imgTd = document.createElement('td');
    const img = document.createElement('img');
    const src = (p.imagem && p.imagem.trim() !== '') ? p.imagem : '/placeholder.jpg';
    img.src = src;
    img.onerror = function(){{ this.src = '/placeholder.jpg'; }};
    imgTd.appendChild(img);
    tr.appendChild(imgTd);

    const codTd = document.createElement('td');
    const codInput = document.createElement('input');
    codInput.type = 'text';
    codInput.value = p.codigo || '';
    codInput.oninput = e => {{ p.codigo = e.target.value; }};
    codTd.appendChild(codInput);
    tr.appendChild(codTd);

    const titTd = document.createElement('td');
    const titArea = document.createElement('textarea');
    titArea.value = p.titulo || '';
    titArea.rows = 2;
    titArea.oninput = e => {{ p.titulo = e.target.value; }};
    titTd.appendChild(titArea);
    tr.appendChild(titTd);

    const precoTd = document.createElement('td');
    const precoInput = document.createElement('input');
    precoInput.type = 'text';
    precoInput.value = p.preco || '';
    precoInput.oninput = e => {{ p.preco = e.target.value; }};
    precoTd.appendChild(precoInput);
    tr.appendChild(precoTd);

    const acTd = document.createElement('td');
    const btnSave = document.createElement('button');
    btnSave.className = 'btn-save';
    btnSave.textContent = 'Salvar';
    btnSave.onclick = () => showMsg('Produto salvo (localmente).');
    const btnDel = document.createElement('button');
    btnDel.className = 'btn-remove';
    btnDel.textContent = 'Excluir';
    btnDel.onclick = () => removeProduto(page, i);
    acTd.appendChild(btnSave);
    acTd.appendChild(btnDel);
    tr.appendChild(acTd);

    tbody.appendChild(tr);
  }});

  const pag = document.getElementById('pagination');
  pag.innerHTML = '';
  const totalPages = Object.keys(PAGES_DATA).length;
  for(let i=1;i<=totalPages;i++) {{
    const btn = document.createElement('button');
    btn.className = 'btn-save-all';
    btn.style.margin = '4px';
    btn.textContent = i;
    if(i === page) btn.style.background = '#0056b3';
    btn.onclick = () => loadPage(i);
    pag.appendChild(btn);
  }}
}}

function showMsg(text){{
  const el = document.getElementById('msg');
  el.textContent = text;
  setTimeout(() => {{ el.textContent = ''; }}, 1500);
}}

function addProduto(){{
  if(!PAGES_DATA[currentPage]) PAGES_DATA[currentPage] = [];
  PAGES_DATA[currentPage].push({{codigo:'', titulo:'', preco:'', imagem:''}});
  loadPage(currentPage);
}}

function removeProduto(page, i){{
  if(confirm('Excluir produto?')){{
    PAGES_DATA[page].splice(i,1);
    loadPage(page);
  }}
}}

function saveAll(){{
  showMsg('💾 Salvando todas (localmente)...');
}}

function exportJSON(){{
  const blob = new Blob([JSON.stringify(PAGES_DATA, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'catalogo_corrigido.json';
  a.click();
  showMsg('✅ JSON exportado com sucesso!');
}}

loadPage(1);
</script>
</body>
</html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
    print(f"✅ HTML interativo criado → {out_html}")


if __name__ == "__main__":
    import sys

    upload_id = sys.argv[1] if len(sys.argv) > 1 else ""
    generate_html(upload_id)