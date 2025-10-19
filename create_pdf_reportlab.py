
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf_from_text(text_file, pdf_file):
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    y_position = 750
    with open(text_file, "r") as f:
        for line in f:
            c.drawString(50, y_position, line.strip())
            y_position -= 14
            if y_position < 50:  # Nova página se o texto atingir o final da página
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = 750
                
    c.save()

create_pdf_from_text("dummy_processo.txt", "dummy_processo.pdf")

