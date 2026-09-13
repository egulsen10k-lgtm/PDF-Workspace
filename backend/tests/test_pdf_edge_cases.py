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

def test_pdf_inspect_edge_cases(tmp_path):
    # 1. Non-existent file path
    res = PDFService.inspect_pdf(str(tmp_path / "non_existent.pdf"))
    assert res["has_custom_fonts"] is False
    assert res["is_encrypted"] is False

    # 2. Corrupted file
    corrupt_path = str(tmp_path / "corrupt.pdf")
    with open(corrupt_path, "wb") as f:
        f.write(b"NOT A REAL PDF FILE HEADER")
    res_corrupt = PDFService.inspect_pdf(corrupt_path)
    assert res_corrupt["has_custom_fonts"] is False

def test_page_count_edge_cases(tmp_path):
    # Invalid PDF file should raise exception or fallback gracefully
    corrupt_path = str(tmp_path / "corrupt.pdf")
    with open(corrupt_path, "wb") as f:
        f.write(b"INVALID PDF DATA")
    with pytest.raises(Exception):
        PDFService.get_page_count(corrupt_path)

def test_render_page_preview_out_of_bounds(tmp_path):
    pdf_path = str(tmp_path / "valid.pdf")
    with open(pdf_path, "wb") as f:
        f.write(create_sample_pdf(2))

    # Page 99 (out of range) should render fallback or handle without crash
    preview_bytes = PDFService.render_page_preview(pdf_path, page_number=99)
    assert isinstance(preview_bytes, bytes)
    assert len(preview_bytes) > 0

def test_split_by_range_edge_cases(tmp_path):
    pdf_path = str(tmp_path / "valid.pdf")
    with open(pdf_path, "wb") as f:
        f.write(create_sample_pdf(3))

    # Out of range, e.g. "10-20" or "99"
    splits = PDFService.split_pdf_by_range(pdf_path, "10-20, 99, 1-2")
    assert isinstance(splits, list)
    # 1-2 range produces split part
    assert len(splits) >= 1

def test_reorder_rotate_out_of_bounds(tmp_path):
    pdf_path = str(tmp_path / "valid.pdf")
    with open(pdf_path, "wb") as f:
        f.write(create_sample_pdf(2))

    # Page index 999 is out of bounds and should be ignored without crash
    items = [{"page_index": 0, "rotation": 90}, {"page_index": 999, "rotation": 180}]
    output_bytes = PDFService.reorder_rotate_pages(pdf_path, items)
    reader = PdfReader(io.BytesIO(output_bytes))
    assert len(reader.pages) == 1

def test_watermark_positions_and_colors(tmp_path):
    pdf_path = str(tmp_path / "valid.pdf")
    with open(pdf_path, "wb") as f:
        f.write(create_sample_pdf(1))

    for pos in ["center", "top-left", "bottom-right", "repeat"]:
        wm_bytes = PDFService.watermark_pdf(pdf_path, text="CONFIDENTIAL", position=pos, opacity=0.1)
        reader = PdfReader(io.BytesIO(wm_bytes))
        assert len(reader.pages) == 1

def test_redact_area_out_of_bounds(tmp_path):
    pdf_path = str(tmp_path / "valid.pdf")
    with open(pdf_path, "wb") as f:
        f.write(create_sample_pdf(1))

    # Area coordinates outside typical page dimensions
    areas = [{"page": 1, "x": 10000, "y": 10000, "width": 500, "height": 500}]
    redacted_bytes = PDFService.redact_pdf(pdf_path, areas=areas)
    reader = PdfReader(io.BytesIO(redacted_bytes))
    assert len(reader.pages) == 1
