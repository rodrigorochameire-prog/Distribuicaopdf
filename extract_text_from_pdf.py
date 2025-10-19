import sys
from PyPDF2 import PdfReader

def extract_text(pdf_path, output_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Texto extraído de {pdf_path} e salvo em {output_path}")
    except Exception as e:
        print(f"Erro ao extrair texto do PDF {pdf_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 extract_text_from_pdf.py <caminho_do_pdf> <caminho_do_arquivo_de_saida>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2]
    extract_text(pdf_path, output_path)

