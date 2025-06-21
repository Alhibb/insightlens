import os
from pypdf import PdfReader
from docx import Document as DocxDocument

def load_pdf(file_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""
    return text

def load_docx(file_path: str) -> str:
    text = ""
    try:
        doc = DocxDocument(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX {file_path}: {e}")
        return ""
    return text

def load_txt(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT {file_path}: {e}")
        return ""

def load_document(file_path: str) -> str | None:
    _, extension = os.path.splitext(file_path.lower())
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    print(f"Loading document: {file_path}")
    if extension == ".pdf":
        return load_pdf(file_path)
    elif extension == ".docx":
        return load_docx(file_path)
    elif extension == ".txt" or extension == ".md":
        return load_txt(file_path)
    else:
        print(f"Unsupported file type: {extension}")
        return None