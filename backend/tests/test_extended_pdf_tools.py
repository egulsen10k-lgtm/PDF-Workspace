import os
import io
import pytest
from pypdf import PdfReader, PdfWriter
from app.services.pdf_service import PDFService

def create_sample_pdf(num_pages: int = 2, text: str = "Sample Document") -> str:
    writer = PdfWriter()
    for i in range(num_pages):
        page = writer.add_blank_page(width=612, height=792)
    tmp_path = f"/tmp/test_ext_sample_{os.urandom(4).hex()}.pdf"
    with open(tmp_path, "wb") as f:
        writer.write(f)
    return tmp_path

def test_rotate_pdf():
    pdf_path = create_sample_pdf(2)
    try:
        rotated = PDFService.rotate_pdf(pdf_path, angle=90, page_selection="all")
        reader = PdfReader(io.BytesIO(rotated))
        assert len(reader.pages) == 2
        assert reader.pages[0].rotation == 90
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_crop_pdf():
    pdf_path = create_sample_pdf(1)
    try:
        cropped = PDFService.crop_pdf(pdf_path, top_pct=10, bottom_pct=10, left_pct=10, right_pct=10)
        reader = PdfReader(io.BytesIO(cropped))
        assert len(reader.pages) == 1
        assert float(reader.pages[0].mediabox.width) < 612
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_add_page_numbers():
    pdf_path = create_sample_pdf(3)
    try:
        numbered = PDFService.add_page_numbers(pdf_path, format_str="Page {page} of {total}", position="bottom-center")
        reader = PdfReader(io.BytesIO(numbered))
        assert len(reader.pages) == 3
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_repair_pdf():
    pdf_path = create_sample_pdf(2)
    try:
        repaired = PDFService.repair_pdf(pdf_path)
        reader = PdfReader(io.BytesIO(repaired))
        assert len(reader.pages) == 2
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_pdf_to_pdfa():
    pdf_path = create_sample_pdf(1)
    try:
        pdfa = PDFService.pdf_to_pdfa(pdf_path)
        reader = PdfReader(io.BytesIO(pdfa))
        assert len(reader.pages) == 1
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_html_to_pdf():
    html_content = "<h1>Invoice</h1><p>Thank you for your business. Total: $100</p>"
    pdf_bytes = PDFService.html_to_pdf(html_content, title="Invoice #101")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1

def test_pdf_to_word():
    pdf_path = create_sample_pdf(1)
    try:
        docx_bytes = PDFService.pdf_to_word(pdf_path)
        assert len(docx_bytes) > 0
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_pdf_to_excel():
    pdf_path = create_sample_pdf(1)
    try:
        xlsx_bytes = PDFService.pdf_to_excel(pdf_path)
        assert len(xlsx_bytes) > 0
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_pdf_to_powerpoint():
    pdf_path = create_sample_pdf(2)
    try:
        pptx_bytes = PDFService.pdf_to_powerpoint(pdf_path)
        assert len(pptx_bytes) > 0
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_pdf_to_markdown():
    pdf_path = create_sample_pdf(1)
    try:
        md_text = PDFService.pdf_to_markdown(pdf_path)
        assert "# Extracted PDF Content" in md_text
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_edit_pdf_annotations():
    pdf_path = create_sample_pdf(1)
    try:
        edited = PDFService.edit_pdf(pdf_path, [
            {"type": "text", "page": 1, "x": 50, "y": 50, "content": "Approved Note", "font_size": 14},
            {"type": "rect", "page": 1, "x": 100, "y": 100, "width": 150, "height": 50},
            {"type": "highlight", "page": 1, "x": 100, "y": 200, "width": 200, "height": 20}
        ])
        reader = PdfReader(io.BytesIO(edited))
        assert len(reader.pages) == 1
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_protect_and_unlock_pdf():
    pdf_path = create_sample_pdf(1)
    try:
        # Encrypt
        encrypted = PDFService.protect_pdf(pdf_path, user_password="secretpassword")
        enc_reader = PdfReader(io.BytesIO(encrypted))
        assert enc_reader.is_encrypted

        # Save encrypted to tmp
        enc_path = f"/tmp/test_enc_{os.urandom(4).hex()}.pdf"
        with open(enc_path, "wb") as f:
            f.write(encrypted)

        # Decrypt
        decrypted = PDFService.unlock_pdf(enc_path, password="secretpassword")
        dec_reader = PdfReader(io.BytesIO(decrypted))
        assert not dec_reader.is_encrypted
        assert len(dec_reader.pages) == 1

        if os.path.exists(enc_path):
            os.remove(enc_path)
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_compare_pdfs():
    pdf_a = create_sample_pdf(1)
    pdf_b = create_sample_pdf(1)
    try:
        res = PDFService.compare_pdfs(pdf_a, pdf_b)
        assert "similarity_percentage" in res
        assert res["doc_a_pages"] == 1
        assert res["doc_b_pages"] == 1
    finally:
        if os.path.exists(pdf_a):
            os.remove(pdf_a)
        if os.path.exists(pdf_b):
            os.remove(pdf_b)
