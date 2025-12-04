import os
import cv2
import numpy as np
import traceback

def preprocess_image(input_path, output_path, apply_denoise=True, apply_clahe=True):
    """
    Pré-processamento padrão para páginas de catálogo.

    Pipeline aplicado:
        - carregamento seguro via OpenCV
        - conversão para escala de cinza
        - equalização adaptativa (CLAHE) opcional
        - remoção de ruído (fastNlMeans) opcional
        - binarização adaptativa
        - normalização do tamanho (mantém resolução original)
        - salvamento em JPG otimizado

    Args:
        input_path (str): Caminho da imagem original (JPG).
        output_path (str): Caminho da imagem pré-processada.
        apply_denoise (bool): Remove ruído com algoritmo rápido.
        apply_clahe   (bool): Equalização adaptativa de contraste.

    Returns:
        dict: resultado com status, paths e erro (se existir).
    """

    result = {
        "status": "error",
        "input_path": input_path,
        "output_path": output_path,
        "error": None
    }

    try:
        if not os.path.exists(input_path):
            result["error"] = f"Arquivo de entrada não existe: {input_path}"
            return result

        # ---- Carregar imagem ----
        img = cv2.imread(input_path)
        if img is None:
            result["error"] = f"Falha ao carregar imagem: {input_path}"
            return result

        # ---- Converter para escala de cinza ----
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ---- Equalização adaptativa (CLAHE) ----
        if apply_clahe:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)

        # ---- Denoise (remoção de ruído) ----
        if apply_denoise:
            gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

        # ---- Binarização adaptativa ----
        processed = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5
        )

        # ---- Salvar output ----
        out_dir = os.path.dirname(output_path)
        os.makedirs(out_dir, exist_ok=True)
        cv2.imwrite(output_path, processed, [cv2.IMWRITE_JPEG_QUALITY, 95])

        result["status"] = "success"
        return result

    except Exception as e:
        result["error"] = str(e)
        result["traceback"] = traceback.format_exc()
        return result
