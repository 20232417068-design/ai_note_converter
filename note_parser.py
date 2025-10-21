from PyPDF2 import PdfReader

def pdf_to_text(uploaded_pdf):
    text = ""
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()
