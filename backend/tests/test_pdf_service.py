import os
import io
import pytest
from reportlab.pdfgen import canvas
from pypdf import PdfReader
from app.services.pdf_service import PDFService

def create_sample_pdf(num_pages: int = 2) -> bytes:
    buf = io.BytesIO()
    can = canvas.Canvas(buf)
    for i in range(1, num_pages + 1):
        can.setFont("Helvetica", 14)
        can.drawString(100, 700, f"Sample Document Page {i}")
        can.showPage()
    can.save()
    return buf.getvalue()

def test_inspect_and_get_page_count(tmp_path):
    pdf_bytes = create_sample_pdf(3)
    file_path = str(tmp_path / "test.pdf")
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    count = PDFService.get_page_count(file_path)
    assert count == 3

    inspection = PDFService.inspect_pdf(file_path)
    assert isinstance(inspection, dict)
    assert "warnings" in inspection
    assert "has_custom_fonts" in inspection

def test_merge_pdfs(tmp_path):
    pdf1 = str(tmp_path / "pdf1.pdf")
    pdf2 = str(tmp_path / "pdf2.pdf")
    with open(pdf1, "wb") as f:
        f.write(create_sample_pdf(2))
    with open(pdf2, "wb") as f:
        f.write(create_sample_pdf(3))

    merged_bytes = PDFService.merge_pdfs([pdf1, pdf2])
    reader = PdfReader(io.BytesIO(merged_bytes))
    assert len(reader.pages) == 5

def test_split_pdf_by_range(tmp_path):
    pdf1 = str(tmp_path / "pdf1.pdf")
    with open(pdf1, "wb") as f:
        f.write(create_sample_pdf(4))

    splits = PDFService.split_pdf_by_range(pdf1, "1-2, 3-4")
    assert len(splits) == 2
    r1 = PdfReader(io.BytesIO(splits[0][1]))
    assert len(r1.pages) == 2

def test_watermark_pdf(tmp_path):
    pdf1 = str(tmp_path / "pdf1.pdf")
    with open(pdf1, "wb") as f:
        f.write(create_sample_pdf(1))

    wm_bytes = PDFService.watermark_pdf(pdf1, text="TEST WATERMARK")
    reader = PdfReader(io.BytesIO(wm_bytes))
    assert len(reader.pages) == 1

def test_redact_pdf(tmp_path):
    pdf1 = str(tmp_path / "pdf1.pdf")
    with open(pdf1, "wb") as f:
        f.write(create_sample_pdf(1))

    redacted_bytes = PDFService.redact_pdf(pdf1, areas=[{"page": 1, "x": 10, "y": 10, "width": 100, "height": 50}])
    reader = PdfReader(io.BytesIO(redacted_bytes))
    assert len(reader.pages) == 1
