
from fpdf2 import FPDF

def create_pdf_from_text(text_file, pdf_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    with open(text_file, "r") as f:
        for line in f:
            pdf.cell(200, 10, txt=line, ln=True, align='L')
            
    pdf.output(pdf_file)

create_pdf_from_text("dummy_processo.txt", "dummy_processo.pdf")

