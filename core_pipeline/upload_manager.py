import os
import shutil

BASE_UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")

def upload_pdf(fornecedor: str, pdf_path: str):
    """
    Faz upload (cópia) de um arquivo PDF local para o diretório do fornecedor.
    Exemplo:
        upload_pdf("ttbrasil", "/home/ubuntu/Downloads/TABELA_TTBRASIL.pdf")
    """
    if not os.path.exists(pdf_path):
        print(f"❌ Arquivo não encontrado: {pdf_path}")
        return

    dest_dir = os.path.join(BASE_UPLOAD_DIR, fornecedor)
    os.makedirs(dest_dir, exist_ok=True)

    dest_file = os.path.join(dest_dir, os.path.basename(pdf_path))
    shutil.copy2(pdf_path, dest_file)

    print(f"✅ Upload concluído: {dest_file}")
    return dest_file

if __name__ == "__main__":
    fornecedor = input("Digite o nome do fornecedor: ").strip().lower()
    pdf_path = input("Digite o caminho completo do PDF: ").strip()
    upload_pdf(fornecedor, pdf_path)
