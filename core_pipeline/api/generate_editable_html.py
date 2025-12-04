import os
import json
import traceback


def generate_editable_html(catalog_json_path, output_html_path, title="Catálogo Extraído - Editável"):
    """
    Gera um HTML editável a partir do catalog_raw.json gerado pelo pipeline.

    Entrada esperada (catalog_json_path):
        Lista de produtos no formato:
        [
          {
            "code": "CT12345" | None,
            "description": "Produto Exemplo" | None,
            "price_value": 12.34 | None,
            "price_text": "12,34" | None,
            "image_path": "crops/page_03/product_0012.jpg" | None,
            "page_index": int | None,
            "column_index": int | None,
            "block_id": int | None,
            "bbox": [x1, y1, x2, y2] | None
          },
          ...
        ]

    Saída:
        - HTML único, estático, com:
            - imagem do produto
            - campos editáveis (código, descrição, preço)
            - botão para exportar JSON atualizado (pronto para integração com ML)

    Retorna:
        dict com status, output_html_path, erro (se houver).
    """

    result = {
        "status": "error",
        "catalog_json_path": catalog_json_path,
        "output_html_path": output_html_path,
        "error": None
    }

    try:
        if not os.path.exists(catalog_json_path):
            result["error"] = f"Arquivo JSON de catálogo não encontrado: {catalog_json_path}"
            return result

        with open(catalog_json_path, "r", encoding="utf-8") as f:
            products = json.load(f)

        if not isinstance(products, list):
            result["error"] = "Formato inválido em catalog_json: esperado uma lista de produtos."
            return result

        # Garante diretório de saída
        out_dir = os.path.dirname(output_html_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        # Monta HTML completo
        html_parts = []

        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='pt-BR'>")
        html_parts.append("<head>")
        html_parts.append("  <meta charset='UTF-8'>")
        html_parts.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_parts.append(f"  <title>{title}</title>")
        html_parts.append("  <style>")
        # CSS simples, focado em usabilidade
        html_parts.append("""
            body {
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin: 0;
                padding: 16px;
                background: #f5f5f5;
            }
            h1 {
                margin: 0 0 8px 0;
                font-size: 22px;
            }
            .top-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                flex-wrap: wrap;
                gap: 8px;
            }
            .top-bar .info {
                font-size: 13px;
                color: #555;
            }
            .btn {
                padding: 8px 14px;
                border-radius: 4px;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-primary {
                background: #007bff;
                color: #fff;
            }
            .btn-secondary {
                background: #e0e0e0;
                color: #333;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                background: #fff;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }
            thead {
                background: #f0f0f0;
            }
            th, td {
                padding: 8px;
                border-bottom: 1px solid #ddd;
                vertical-align: top;
                font-size: 13px;
            }
            th {
                text-align: left;
                font-weight: 600;
            }
            tr:nth-child(even) td {
                background: #fafafa;
            }
            img.product-thumb {
                max-width: 120px;
                max-height: 120px;
                object-fit: contain;
                border-radius: 4px;
                border: 1px solid #ddd;
                background: #fff;
            }
            input[type="text"], input[type="number"], textarea {
                width: 100%;
                box-sizing: border-box;
                padding: 4px 6px;
                font-size: 13px;
                border-radius: 4px;
                border: 1px solid #ccc;
            }
            textarea {
                min-height: 60px;
                resize: vertical;
            }
            .meta-label {
                font-size: 11px;
                color: #666;
            }
            .meta-value {
                font-size: 11px;
                color: #333;
            }
            .price-container {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .price-container small {
                font-size: 11px;
                color: #666;
            }
            .footer-info {
                margin-top: 16px;
                font-size: 11px;
                color: #777;
            }
            .counter {
                font-size: 13px;
                color: #444;
            }
        """)
        html_parts.append("  </style>")
        html_parts.append("</head>")
        html_parts.append("<body>")

        # Barra superior
        html_parts.append("<div class='top-bar'>")
        html_parts.append("  <div>")
        html_parts.append("    <h1>Catálogo extraído - Edição para Mercado Livre</h1>")
        html_parts.append("    <div class='info'>Edite código, descrição e preço. Em seguida, exporte o JSON pronto para integração.</div>")
        html_parts.append("  </div>")
        html_parts.append("  <div>")
        html_parts.append("    <button class='btn btn-secondary' type='button' onclick='recarregarDaPagina()'>Recarregar página</button>")
        html_parts.append("    <button class='btn btn-primary' type='button' onclick='exportarJSON()'>Exportar JSON editado</button>")
        html_parts.append("  </div>")
        html_parts.append("</div>")

        html_parts.append(f"<div class='counter'>Total de produtos: <span id='total-produtos'>{len(products)}</span></div>")

        # Tabela de produtos
        html_parts.append("<table>")
        html_parts.append("  <thead>")
        html_parts.append("    <tr>")
        html_parts.append("      <th>Imagem</th>")
        html_parts.append("      <th>Código</th>")
        html_parts.append("      <th>Descrição</th>")
        html_parts.append("      <th>Preço</th>")
        html_parts.append("      <th>Metadados</th>")
        html_parts.append("    </tr>")
        html_parts.append("  </thead>")
        html_parts.append("  <tbody>")

        for idx, p in enumerate(products):
            code = p.get("code") or ""
            desc = p.get("description") or ""
            price_value = p.get("price_value")
            price_text = p.get("price_text") or ""
            image_path = p.get("image_path") or ""
            page_index = p.get("page_index")
            column_index = p.get("column_index")
            block_id = p.get("block_id")
            bbox = p.get("bbox")

            # Normaliza tipos simples para exibição
            price_value_str = "" if price_value is None else str(price_value)
            page_str = "" if page_index is None else str(page_index)
            col_str = "" if column_index is None else str(column_index)
            block_str = "" if block_id is None else str(block_id)
            bbox_str = json.dumps(bbox) if bbox is not None else "null"

            html_parts.append(f"    <tr data-index='{idx}' data-bbox='{bbox_str}'>")

            # Coluna imagem
            html_parts.append("      <td>")
            if image_path:
                html_parts.append(f"        <img class='product-thumb' src='{image_path}' alt='produto {idx}'>")
                html_parts.append(f"        <div class='meta-label'>path:</div>")
                html_parts.append(f"        <div class='meta-value'>{image_path}</div>")
            else:
                html_parts.append("        <span class='meta-label'>sem imagem</span>")
            html_parts.append("      </td>")

            # Coluna código
            html_parts.append("      <td>")
            html_parts.append(f"        <input type='text' name='code' value='{code}' />")
            html_parts.append("      </td>")

            # Coluna descrição
            html_parts.append("      <td>")
            html_parts.append(f"        <textarea name='description'>{desc}</textarea>")
            html_parts.append("      </td>")

            # Coluna preço
            html_parts.append("      <td>")
            html_parts.append("        <div class='price-container'>")
            html_parts.append("          <label class='meta-label'>Preço numérico (para envio):</label>")
            html_parts.append(f"          <input type='number' step='0.01' name='price_value' value='{price_value_str}' />")
            html_parts.append("          <label class='meta-label'>Texto original de preço (opcional):</label>")
            html_parts.append(f"          <input type='text' name='price_text' value='{price_text}' />")
            html_parts.append("        </div>")
            html_parts.append("      </td>")

            # Coluna metadados
            html_parts.append("      <td>")
            html_parts.append("        <div class='meta-label'>Página:</div>")
            html_parts.append(f"        <div class='meta-value'><input type='text' name='page_index' value='{page_str}' /></div>")
            html_parts.append("        <div class='meta-label'>Coluna:</div>")
            html_parts.append(f"        <div class='meta-value'><input type='text' name='column_index' value='{col_str}' /></div>")
            html_parts.append("        <div class='meta-label'>Bloco:</div>")
            html_parts.append(f"        <div class='meta-value'><input type='text' name='block_id' value='{block_str}' /></div>")
            html_parts.append("      </td>")

            html_parts.append("    </tr>")

        html_parts.append("  </tbody>")
        html_parts.append("</table>")

        # Rodapé
        html_parts.append("""
            <div class="footer-info">
                Ao clicar em <b>Exportar JSON editado</b>, será baixado um arquivo JSON contendo todos os produtos
                com os campos atualizados. Esse arquivo é o ponto de partida para montagem do payload do Mercado Livre.
            </div>
        """)

        # Script JS para coleta e exportação do JSON
        html_parts.append("<script>")
        html_parts.append("""
        function recarregarDaPagina() {
            if (confirm("Descartar alterações e recarregar a página?")) {
                window.location.reload();
            }
        }

        function exportarJSON() {
            const rows = document.querySelectorAll("tbody tr");
            const data = [];

            rows.forEach((row) => {
                const idx = parseInt(row.getAttribute("data-index"), 10);
                const bboxAttr = row.getAttribute("data-bbox");
                let bbox = null;
                try {
                    bbox = JSON.parse(bboxAttr);
                } catch (e) {
                    bbox = null;
                }

                const inputCode = row.querySelector("input[name='code']");
                const inputDesc = row.querySelector("textarea[name='description']");
                const inputPriceVal = row.querySelector("input[name='price_value']");
                const inputPriceText = row.querySelector("input[name='price_text']");
                const inputPage = row.querySelector("input[name='page_index']");
                const inputCol = row.querySelector("input[name='column_index']");
                const inputBlock = row.querySelector("input[name='block_id']");

                const code = inputCode ? inputCode.value.trim() : null;
                const description = inputDesc ? inputDesc.value.trim() : null;
                const price_value_str = inputPriceVal ? inputPriceVal.value.trim() : "";
                const price_text = inputPriceText ? inputPriceText.value.trim() : null;

                let price_value = null;
                if (price_value_str !== "") {
                    const n = Number(price_value_str.replace(",", "."));
                    if (!Number.isNaN(n)) {
                        price_value = n;
                    }
                }

                const page_index_str = inputPage ? inputPage.value.trim() : "";
                const column_index_str = inputCol ? inputCol.value.trim() : "";
                const block_id_str = inputBlock ? inputBlock.value.trim() : "";

                const page_index = page_index_str === "" ? null : Number(page_index_str);
                const column_index = column_index_str === "" ? null : Number(column_index_str);
                const block_id = block_id_str === "" ? null : Number(block_id_str);

                // Tenta recuperar o caminho da imagem pelo alt ou pelo path mostrado
                let image_path = null;
                const img = row.querySelector("img.product-thumb");
                if (img && img.getAttribute("src")) {
                    image_path = img.getAttribute("src");
                } else {
                    // fallback: tenta ler texto do path exibido
                    const metaValues = row.querySelectorAll(".meta-value");
                    metaValues.forEach((el) => {
                        if (!image_path && el.textContent && el.textContent.trim() !== "") {
                            image_path = el.textContent.trim();
                        }
                    });
                }

                data.push({
                    code: code || null,
                    description: description || null,
                    price_value: price_value,
                    price_text: price_text || null,
                    image_path: image_path || null,
                    page_index: Number.isNaN(page_index) ? null : page_index,
                    column_index: Number.isNaN(column_index) ? null : column_index,
                    block_id: Number.isNaN(block_id) ? null : block_id,
                    bbox: bbox
                });
            });

            const jsonStr = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonStr], { type: "application/json" });

            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;

            const now = new Date();
            const ts = now.toISOString().replace(/[:.]/g, "-");
            a.download = "catalog_editado_" + ts + ".json";

            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        """)
        html_parts.append("</script>")

        html_parts.append("</body>")
        html_parts.append("</html>")

        html_str = "\n".join(html_parts)

        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_str)

        result["status"] = "success"
        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result
