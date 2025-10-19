from PyPDF2 import PdfReader
import sys

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Erro ao extrair texto do PDF: {e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        extracted_text = extract_text_from_pdf(pdf_file)
        with open("/home/ubuntu/extracted_text.txt", "w", encoding="utf-8") as f:
            f.write(extracted_text)
    else:
        print("Uso: python3 extract_pdf_text.py <caminho_do_pdf>")
