import os
import json
import traceback

import cv2
import numpy as np


def _load_image_as_binary(image_path):
    """
    Carrega imagem e aplica uma binarização robusta para segmentação.

    Retorna:
        bin_img (uint8): imagem binária (0/255)
        original (BGR): imagem original
    """
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Falha ao carregar imagem: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binarização adaptativa (funciona bem para catálogos com variação de iluminação)
    bin_img = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,  # invertida: texto/elementos = 255
        31,
        5,
    )

    # Pequena abertura para limpar ruídos isolados
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=1)

    return bin_img, img


def _find_connected_components(bin_img):
    """
    Encontra componentes conectados na imagem binária e retorna bounding boxes.

    Retorna:
        boxes: lista de (x, y, w, h)
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bin_img, connectivity=8)

    boxes = []
    for label in range(1, num_labels):  # ignora background (0)
        x, y, w, h, area = stats[label]
        # Filtra ruídos muito pequenos
        if area < 30:
            continue
        boxes.append((x, y, w, h))

    return boxes


def _kmeans_1d(points, k, max_iter=50):
    """
    Implementação simples e determinística de KMeans 1D.

    Args:
        points (np.ndarray): vetor 1D de pontos (float ou int).
        k (int): número de clusters.

    Retorna:
        centers (np.ndarray): centros ordenados (k,)
        labels (np.ndarray): índice do cluster para cada ponto (len(points),)
    """
    points = np.asarray(points, dtype=float)
    if len(points) == 0:
        return np.array([]), np.array([])

    unique_points = np.unique(points)
    if len(unique_points) <= k:
        # Cada ponto único vira um cluster
        centers = unique_points
        labels = np.zeros_like(points, dtype=int)
        for i, p in enumerate(points):
            labels[i] = int(np.where(centers == p)[0][0])
        return centers, labels

    # Inicialização determinística: centros igualmente espaçados no intervalo [min, max]
    p_min, p_max = float(points.min()), float(points.max())
    centers = np.linspace(p_min, p_max, k)

    for _ in range(max_iter):
        # Atribuição
        dists = np.abs(points.reshape(-1, 1) - centers.reshape(1, -1))
        labels = np.argmin(dists, axis=1)

        new_centers = np.zeros_like(centers)
        for ci in range(k):
            cluster_points = points[labels == ci]
            if len(cluster_points) == 0:
                # Se cluster vazio, mantém centro anterior (evita instabilidade)
                new_centers[ci] = centers[ci]
            else:
                new_centers[ci] = cluster_points.mean()

        if np.allclose(new_centers, centers):
            break
        centers = new_centers

    # Ordena centros e realinha labels
    order = np.argsort(centers)
    centers = centers[order]
    remap = {old: new for new, old in enumerate(order)}
    labels = np.array([remap[l] for l in labels], dtype=int)

    return centers, labels


def _estimate_column_count(image_width, min_col_width=250, max_cols=5):
    """
    Estima número razoável de colunas com base na largura da página.
    """
    estimated = max(1, int(image_width / max(min_col_width, 1)))
    return max(1, min(estimated, max_cols))


def _cluster_columns_from_boxes(boxes, img_width):
    """
    Agrupa bounding boxes de componentes em colunas usando KMeans 1D
    nos centros em X.

    Retorna:
        columns: lista de dicionários:
            {
                "column_index": int,
                "x1": int,
                "x2": int,
            }
    """
    if not boxes:
        return []

    centers_x = np.array([x + w / 2.0 for (x, _, w, _) in boxes], dtype=float)

    k = _estimate_column_count(img_width)
    centers, labels = _kmeans_1d(centers_x, k)

    if len(centers) == 0:
        # Fallback: uma coluna cobrindo a página inteira
        return [
            {
                "column_index": 0,
                "x1": 0,
                "x2": img_width - 1,
            }
        ]

    columns = []
    for ci in range(len(centers)):
        # Coleta todos os boxes deste cluster e pega min/max em X
        xs = []
        xe = []
        for (box, lab) in zip(boxes, labels):
            if lab != ci:
                continue
            x, _, w, _ = box
            xs.append(x)
            xe.append(x + w)
        if not xs:
            continue

        col_x1 = int(min(xs))
        col_x2 = int(max(xe))

        # Margem mínima para garantir cobertura visual suficientemente larga
        margin = max(5, int(0.01 * img_width))
        col_x1 = max(0, col_x1 - margin)
        col_x2 = min(img_width - 1, col_x2 + margin)

        columns.append(
            {
                "column_index": ci,
                "x1": col_x1,
                "x2": col_x2,
            }
        )

    # Ordenar colunas da esquerda para direita
    columns.sort(key=lambda c: c["x1"])
    # Ajustar índices para sequência contínua
    for idx, col in enumerate(columns):
        col["column_index"] = idx

    return columns


def _segment_lines_in_column(bin_img, col_x1, col_x2, min_line_height=20, min_area=100):
    """
    Segmenta linhas em uma coluna usando projeção horizontal.

    Args:
        bin_img: imagem binária (0/255, texto=255) em toda a página.
        col_x1, col_x2: intervalo da coluna.
        min_line_height: altura mínima para considerar uma linha.
        min_area: área mínima (largura * altura) para manter bloco.

    Retorna:
        blocks: lista de dicts com {"y1", "y2", "x1", "x2"}
    """
    h, w = bin_img.shape[:2]
    col_x1 = max(0, min(col_x1, w - 1))
    col_x2 = max(0, min(col_x2, w - 1))
    if col_x2 <= col_x1:
        return []

    # Recorte da coluna
    col_region = bin_img[:, col_x1:col_x2 + 1]

    # Projeção horizontal (soma de pixels brancos na linha)
    proj = np.sum(col_region > 0, axis=1)  # vetor de tamanho h

    # Threshold: linha "ativa" se proj > 0 (ou pequena fração de largura)
    active = proj > 0

    blocks = []
    in_block = False
    start_y = 0

    for y in range(h):
        if active[y]:
            if not in_block:
                in_block = True
                start_y = y
        else:
            if in_block:
                end_y = y - 1
                height = end_y - start_y + 1
                if height >= min_line_height:
                    # bounding box na coluna
                    block_height = height
                    block_width = col_x2 - col_x1 + 1
                    if block_width * block_height >= min_area:
                        blocks.append(
                            {
                                "x1": int(col_x1),
                                "y1": int(start_y),
                                "x2": int(col_x2),
                                "y2": int(end_y),
                            }
                        )
                in_block = False

    # Caso o bloco continue até o final da imagem
    if in_block:
        end_y = h - 1
        height = end_y - start_y + 1
        if height >= min_line_height:
            block_height = height
            block_width = col_x2 - col_x1 + 1
            if block_width * block_height >= min_area:
                blocks.append(
                    {
                        "x1": int(col_x1),
                        "y1": int(start_y),
                        "x2": int(col_x2),
                        "y2": int(end_y),
                    }
                )

    return blocks


def segment_page_into_blocks(image_path, output_json_path=None):
    """
    Segmenta uma página em blocos estruturados (coluna + linha).

    Entrada:
        image_path (str): caminho da página (já pré-processada ou não).
        output_json_path (str|None): se definido, salva JSON com os blocos.

    Saída (dict):
        {
            "status": "success" | "error",
            "image_path": str,
            "blocks": [
                {
                    "id": int,
                    "column_index": int,
                    "bbox": [x1, y1, x2, y2],
                },
                ...
            ],
            "columns": [
                {
                    "column_index": int,
                    "x1": int,
                    "x2": int
                },
                ...
            ],
            "error": str|None
        }
    """
    result = {
        "status": "error",
        "image_path": image_path,
        "blocks": [],
        "columns": [],
        "error": None,
    }

    try:
        if not os.path.exists(image_path):
            result["error"] = f"Imagem não encontrada: {image_path}"
            return result

        bin_img, _ = _load_image_as_binary(image_path)
        h, w = bin_img.shape[:2]

        # 1) Componentes conectados → estimativa visual de colunas
        boxes = _find_connected_components(bin_img)
        columns = _cluster_columns_from_boxes(boxes, w)

        all_blocks = []
        block_id = 0

        # 2) Para cada coluna, segmenta linhas
        for col in columns:
            col_blocks = _segment_lines_in_column(
                bin_img,
                col_x1=col["x1"],
                col_x2=col["x2"],
            )
            for b in col_blocks:
                all_blocks.append(
                    {
                        "id": block_id,
                        "column_index": col["column_index"],
                        "bbox": [int(b["x1"]), int(b["y1"]), int(b["x2"]), int(b["y2"])],
                    }
                )
                block_id += 1

        result["status"] = "success"
        result["blocks"] = all_blocks
        result["columns"] = columns

        # Salvar JSON, se solicitado
        if output_json_path is not None:
            out_dir = os.path.dirname(output_json_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "image": os.path.basename(image_path),
                        "width": w,
                        "height": h,
                        "columns": columns,
                        "blocks": all_blocks,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result
