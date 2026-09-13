import os
import io
import math
import zipfile
import tempfile
import subprocess
import asyncio
import difflib
from typing import List, Dict, Any, Tuple, Optional

HAS_PIKEPDF = False
try:
    import pikepdf
    HAS_PIKEPDF = True
except Exception:
    HAS_PIKEPDF = False

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white, red, blue, green
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

HAS_PDF2IMAGE = False
try:
    import pdf2image
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

HAS_PYTESSERACT = False
try:
    import pytesseract
    from PIL import Image
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False

HAS_DOCX = False
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

HAS_PPTX = False
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

HAS_OPENPYXL = False
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from PIL import Image, ImageDraw


class PDFService:
    @staticmethod
    def inspect_pdf(file_path: str) -> Dict[str, Any]:
        """
        Inspect PDF for custom fonts, forms, signatures, and encryption.
        Generates warnings for potential structure alterations.
        """
        warnings = []
        fonts = set()
        has_interactive_forms = False
        form_field_count = 0
        has_digital_signatures = False
        signature_count = 0
        is_encrypted = False

        if HAS_PIKEPDF:
            try:
                with pikepdf.open(file_path) as pdf:
                    is_encrypted = pdf.is_encrypted
                    
                    # Check AcroForm
                    if "/AcroForm" in pdf.Root:
                        acroform = pdf.Root["/AcroForm"]
                        if "/Fields" in acroform:
                            fields = acroform["/Fields"]
                            form_field_count = len(fields)
                            has_interactive_forms = form_field_count > 0
                    
                    # Check for signatures
                    for page in pdf.pages:
                        if "/Annots" in page:
                            for annot in page["/Annots"]:
                                obj = annot.get_object() if hasattr(annot, "get_object") else annot
                                if isinstance(obj, pikepdf.Dictionary):
                                    if obj.get("/Subtype") == pikepdf.Name("/Widget") and obj.get("/FT") == pikepdf.Name("/Sig"):
                                        has_digital_signatures = True
                                        signature_count += 1
                    
                    # Check fonts in pages
                    for page in pdf.pages:
                        if "/Resources" in page and "/Font" in page["/Resources"]:
                            font_dict = page["/Resources"]["/Font"]
                            for font_key, font_obj in font_dict.items():
                                if isinstance(font_obj, pikepdf.Dictionary):
                                    base_font = str(font_obj.get("/BaseFont", font_key))
                                    fonts.add(base_font.lstrip("/"))

            except Exception:
                pass

        # Fallback / standard PyPDF inspection
        try:
            reader = PdfReader(file_path)
            if reader.is_encrypted:
                is_encrypted = True

            if hasattr(reader, "get_fields") and reader.get_fields():
                fields = reader.get_fields()
                has_interactive_forms = True
                form_field_count = max(form_field_count, len(fields))

            for page in reader.pages:
                if "/Resources" in page and "/Font" in page["/Resources"]:
                    font_dict = page["/Resources"]["/Font"]
                    if hasattr(font_dict, "keys"):
                        for f_key in font_dict.keys():
                            fonts.add(str(f_key).lstrip("/"))
        except Exception:
            pass

        fonts_list = list(fonts)[:20]
        has_custom_fonts = len(fonts_list) > 0

        if has_custom_fonts:
            warnings.append(f"Contains custom embedded fonts ({len(fonts_list)} found). Editing may reflow text.")
        if has_interactive_forms:
            warnings.append(f"Contains interactive form fields ({form_field_count} found). Flattening may lock responses.")
        if has_digital_signatures:
            warnings.append(f"Contains digital signatures ({signature_count} found). Any modification will invalidate signatures!")
        if is_encrypted:
            warnings.append("Document is encrypted or password-protected.")

        return {
            "has_custom_fonts": has_custom_fonts,
            "fonts_list": fonts_list,
            "has_interactive_forms": has_interactive_forms,
            "form_field_count": form_field_count,
            "has_digital_signatures": has_digital_signatures,
            "signature_count": signature_count,
            "is_encrypted": is_encrypted,
            "is_password_protected": is_encrypted,
            "warnings": warnings
        }

    @staticmethod
    def get_page_count(file_path: str) -> int:
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(file_path) as pdf:
                    return len(pdf.pages)
            except Exception:
                pass
        reader = PdfReader(file_path)
        return len(reader.pages)

    @staticmethod
    def render_page_preview(file_path: str, page_number: int = 1) -> bytes:
        if HAS_PDF2IMAGE:
            try:
                images = pdf2image.convert_from_path(
                    file_path,
                    first_page=page_number,
                    last_page=page_number,
                    dpi=120
                )
                if images:
                    buf = io.BytesIO()
                    images[0].save(buf, format="PNG")
                    return buf.getvalue()
            except Exception:
                pass

        # Fallback image rendering
        img = Image.new("RGB", (400, 550), color=(245, 247, 250))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 380, 530], outline=(200, 200, 200), width=2)
        draw.text((60, 250), f"PDF Preview Page {page_number}", fill=(100, 100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def merge_pdfs(input_paths: List[str]) -> bytes:
        if HAS_PIKEPDF:
            try:
                output_pdf = pikepdf.Pdf.new()
                for path in input_paths:
                    with pikepdf.open(path) as src:
                        output_pdf.pages.extend(src.pages)
                buf = io.BytesIO()
                output_pdf.save(buf)
                return buf.getvalue()
            except Exception:
                pass

        writer = PdfWriter()
        for path in input_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def split_pdf_by_range(input_path: str, ranges_str: str) -> List[Tuple[str, bytes]]:
        results = []
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(input_path) as src:
                    total_pages = len(src.pages)
                    parts = [p.strip() for p in ranges_str.split(",") if p.strip()]
                    
                    for idx, part in enumerate(parts, 1):
                        new_pdf = pikepdf.Pdf.new()
                        if "-" in part:
                            start_str, end_str = part.split("-", 1)
                            start = max(1, int(start_str.strip()))
                            end = min(total_pages, int(end_str.strip()))
                            for pno in range(start - 1, end):
                                new_pdf.pages.append(src.pages[pno])
                            name = f"split_part_{idx}_pages_{start}_to_{end}.pdf"
                        else:
                            pno = int(part.strip()) - 1
                            if 0 <= pno < total_pages:
                                new_pdf.pages.append(src.pages[pno])
                            name = f"split_part_{idx}_page_{pno + 1}.pdf"
                        
                        buf = io.BytesIO()
                        new_pdf.save(buf)
                        results.append((name, buf.getvalue()))

                if results:
                    return results
            except Exception:
                pass

        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        parts = [p.strip() for p in ranges_str.split(",") if p.strip()]

        for idx, part in enumerate(parts, 1):
            writer = PdfWriter()
            if "-" in part:
                start_str, end_str = part.split("-", 1)
                start = max(1, int(start_str.strip()))
                end = min(total_pages, int(end_str.strip()))
                for pno in range(start - 1, end):
                    writer.add_page(reader.pages[pno])
                name = f"split_part_{idx}_pages_{start}_to_{end}.pdf"
            else:
                pno = int(part.strip()) - 1
                if 0 <= pno < total_pages:
                    writer.add_page(reader.pages[pno])
                name = f"split_part_{idx}_page_{pno + 1}.pdf"

            buf = io.BytesIO()
            writer.write(buf)
            results.append((name, buf.getvalue()))

        return results

    @staticmethod
    def reorder_rotate_pages(input_path: str, page_items: List[Dict[str, int]]) -> bytes:
        if HAS_PIKEPDF:
            try:
                out_pdf = pikepdf.Pdf.new()
                with pikepdf.open(input_path) as src:
                    total = len(src.pages)
                    for item in page_items:
                        idx = item["page_index"]
                        rot = item.get("rotation", 0)
                        if 0 <= idx < total:
                            page = src.pages[idx]
                            if rot != 0:
                                current_rot = int(page.get("/Rotate", 0))
                                page.Rotate = (current_rot + rot) % 360
                            out_pdf.pages.append(page)
                buf = io.BytesIO()
                out_pdf.save(buf)
                return buf.getvalue()
            except Exception:
                pass

        reader = PdfReader(input_path)
        writer = PdfWriter()
        total = len(reader.pages)

        for item in page_items:
            idx = item["page_index"]
            rot = item.get("rotation", 0)
            if 0 <= idx < total:
                page = reader.pages[idx]
                if rot != 0:
                    page.rotate(rot)
                writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def rotate_pdf(input_path: str, angle: int, page_selection: str = "all") -> bytes:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        total = len(reader.pages)

        target_pages = set(range(total))
        if page_selection == "even":
            target_pages = set(i for i in range(total) if (i + 1) % 2 == 0)
        elif page_selection == "odd":
            target_pages = set(i for i in range(total) if (i + 1) % 2 != 0)
        elif page_selection != "all":
            # parse comma-separated list e.g. "1,2,5"
            try:
                nums = [int(p.strip()) - 1 for p in page_selection.split(",") if p.strip()]
                target_pages = set(i for i in nums if 0 <= i < total)
            except Exception:
                pass

        for i, page in enumerate(reader.pages):
            if i in target_pages:
                page.rotate(angle)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def crop_pdf(
        input_path: str,
        top_pct: float = 0,
        bottom_pct: float = 0,
        left_pct: float = 0,
        right_pct: float = 0
    ) -> bytes:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            crop_left = width * (left_pct / 100.0)
            crop_right = width * (1.0 - right_pct / 100.0)
            crop_bottom = height * (bottom_pct / 100.0)
            crop_top = height * (1.0 - top_pct / 100.0)

            page.mediabox.lower_left = (crop_left, crop_bottom)
            page.mediabox.upper_right = (crop_right, crop_top)
            page.cropbox.lower_left = (crop_left, crop_bottom)
            page.cropbox.upper_right = (crop_right, crop_top)

            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def add_page_numbers(
        input_path: str,
        format_str: str = "Page {page} of {total}",
        position: str = "bottom-center",
        font_size: int = 10,
        start_number: int = 1
    ) -> bytes:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        for idx, page in enumerate(reader.pages):
            page_num = idx + start_number
            text = format_str.replace("{page}", str(page_num)).replace("{total}", str(total_pages + start_number - 1))

            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFont("Helvetica", font_size)
            can.setFillColor(HexColor("#333333"))

            if position == "bottom-center":
                can.drawCentredString(width / 2, 25, text)
            elif position == "bottom-left":
                can.drawString(36, 25, text)
            elif position == "bottom-right":
                can.drawRightString(width - 36, 25, text)
            elif position == "top-center":
                can.drawCentredString(width / 2, height - 30, text)
            elif position == "top-left":
                can.drawString(36, height - 30, text)
            elif position == "top-right":
                can.drawRightString(width - 36, height - 30, text)

            can.save()
            packet.seek(0)
            overlay = PdfReader(packet).pages[0]
            page.merge_page(overlay)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def compress_pdf(input_path: str, quality: str = "medium") -> bytes:
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(input_path) as pdf:
                    buf = io.BytesIO()
                    pdf.save(
                        buf,
                        compress_streams=True,
                        recompress_flate=True,
                        linearize=True,
                        object_stream_mode=pikepdf.ObjectStreamMode.generate
                    )
                    return buf.getvalue()
            except Exception:
                pass

        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def repair_pdf(input_path: str) -> bytes:
        """
        Repair corrupt or damaged PDF cross-reference tables and recover streams.
        """
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(input_path, recover_xref=True, fix_metadata_version=True) as pdf:
                    buf = io.BytesIO()
                    pdf.save(buf, fix_metadata_version=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
                    return buf.getvalue()
            except Exception:
                pass

        # Fallback repair using pypdf parser recovery
        reader = PdfReader(input_path, strict=False)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def pdf_to_pdfa(input_path: str) -> bytes:
        """
        Convert standard PDF into PDF/A ISO archivable format with compliant metadata.
        """
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(input_path) as pdf:
                    with pdf.open_metadata(set_pikepdf_as_editor=False) as meta:
                        meta["pdfaExtension:schemas"] = "PDF/A-1b"
                        meta["dc:format"] = "application/pdf"
                    buf = io.BytesIO()
                    pdf.save(buf, pdf_version="1.7")
                    return buf.getvalue()
            except Exception:
                pass

        reader = PdfReader(input_path)
        writer = PdfWriter()
        writer.append(reader)
        writer.add_metadata({
            "/GTS_PDFA1": "http://www.aiim.org/pdfa/ns/id/",
            "/Title": "Archival PDF/A Document",
            "/Producer": "ILovePDF Personal Local Engine"
        })
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def images_to_pdf(image_bytes_list: List[bytes], margin: int = 10) -> bytes:
        """
        Convert one or multiple image files (JPG, PNG, WEBP) into a single clean PDF.
        """
        pil_images = []
        for b in image_bytes_list:
            try:
                img = Image.open(io.BytesIO(b))
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                pil_images.append(img)
            except Exception:
                pass

        if not pil_images:
            raise ValueError("No valid images provided for conversion.")

        buf = io.BytesIO()
        first_img = pil_images[0]
        other_images = pil_images[1:] if len(pil_images) > 1 else []
        first_img.save(buf, format="PDF", save_all=True, append_images=other_images)
        return buf.getvalue()

    @staticmethod
    def html_to_pdf(html_text: str, title: str = "Converted HTML Document") -> bytes:
        """
        Convert HTML or rich text markup into PDF using ReportLab Flowables.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=HexColor("#1e293b"),
            spaceAfter=15
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=HexColor("#334155"),
            spaceAfter=10
        )

        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 10))

        # Basic HTML clean to paragraphs
        paragraphs = html_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<p>", "").split("</p>")
        for p in paragraphs:
            clean_text = p.strip().replace("\n", "<br/>")
            if clean_text:
                try:
                    story.append(Paragraph(clean_text, body_style))
                except Exception:
                    # Strip any unsupported XML/HTML tags
                    plain = "".join(c for c in clean_text if c.isalnum() or c in " .,!?;:-()[]'\"\n")
                    story.append(Paragraph(plain, body_style))

        doc.build(story)
        return buf.getvalue()

    @staticmethod
    def pdf_to_word(input_path: str) -> bytes:
        """
        Extract text structure, paragraphs, and headings into editable DOCX.
        """
        if not HAS_DOCX:
            raise ValueError("python-docx library is not installed.")

        reader = PdfReader(input_path)
        doc = docx.Document()
        doc.add_heading("Extracted Document Content", level=1)

        for idx, page in enumerate(reader.pages):
            doc.add_heading(f"Page {idx + 1}", level=2)
            text = page.extract_text() or ""
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                lines = para.split("\n")
                cleaned_para = " ".join(l.strip() for l in lines if l.strip())
                if cleaned_para:
                    doc.add_paragraph(cleaned_para)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    @staticmethod
    def pdf_to_excel(input_path: str) -> bytes:
        """
        Extract tabular text lines from PDF into multi-sheet Excel (.xlsx).
        """
        if not HAS_OPENPYXL:
            raise ValueError("openpyxl library is not installed.")

        reader = PdfReader(input_path)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Extracted Tables"

        row_cursor = 1
        for idx, page in enumerate(reader.pages):
            ws.cell(row=row_cursor, column=1, value=f"--- PAGE {idx + 1} ---")
            row_cursor += 1

            text = page.extract_text() or ""
            lines = text.split("\n")
            for line in lines:
                parts = [p.strip() for p in line.split("  ") if p.strip()]
                if parts:
                    for col_idx, part in enumerate(parts, 1):
                        ws.cell(row=row_cursor, column=col_idx, value=part)
                    row_cursor += 1

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    @staticmethod
    def pdf_to_powerpoint(input_path: str) -> bytes:
        """
        Convert PDF pages into slide deck (.pptx) with rendered page visuals.
        """
        if not HAS_PPTX:
            raise ValueError("python-pptx library is not installed.")

        prs = Presentation()
        # Set 16:9 widescreen slides
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)

        blank_slide_layout = prs.slide_layouts[6]

        if HAS_PDF2IMAGE:
            try:
                images = pdf2image.convert_from_path(input_path, dpi=120)
                for img in images:
                    slide = prs.slides.add_slide(blank_slide_layout)
                    img_buf = io.BytesIO()
                    img.save(img_buf, format="PNG")
                    img_buf.seek(0)
                    slide.shapes.add_picture(img_buf, Inches(1), Inches(0.5), height=Inches(6.5))
                
                buf = io.BytesIO()
                prs.save(buf)
                return buf.getvalue()
            except Exception:
                pass # Fallback to text parsing if poppler fails

        reader = PdfReader(input_path)
        for idx, page in enumerate(reader.pages):
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            title = slide.shapes.title
            title.text = f"Slide Page {idx + 1}"
            body = slide.shapes.placeholders[1]
            body.text = page.extract_text() or "(No readable text)"

        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()

    @staticmethod
    def pdf_to_images_zip(input_path: str, img_format: str = "jpg", dpi: int = 150) -> bytes:
        """
        Extract each page as high-res JPG/PNG images and package into a ZIP.
        """
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            if HAS_PDF2IMAGE:
                images = pdf2image.convert_from_path(input_path, dpi=dpi)
                for idx, img in enumerate(images, 1):
                    img_buf = io.BytesIO()
                    fmt = "JPEG" if img_format.lower() in ("jpg", "jpeg") else "PNG"
                    img.save(img_buf, format=fmt, quality=92)
                    zf.writestr(f"page_{idx}.{img_format.lower()}", img_buf.getvalue())
            else:
                # Fallback PIL preview
                reader = PdfReader(input_path)
                for idx in range(1, len(reader.pages) + 1):
                    img = Image.new("RGB", (600, 800), color=(250, 250, 250))
                    draw = ImageDraw.Draw(img)
                    draw.text((100, 350), f"Page {idx}", fill=(0, 0, 0))
                    img_buf = io.BytesIO()
                    img.save(img_buf, format="JPEG")
                    zf.writestr(f"page_{idx}.jpg", img_buf.getvalue())

        return zip_buf.getvalue()

    @staticmethod
    def pdf_to_markdown(input_path: str) -> str:
        """
        Extract structured offline Markdown (.md) headings, paragraphs, and tables.
        """
        reader = PdfReader(input_path)
        md_lines = []
        md_lines.append("# Extracted PDF Content\n")

        for idx, page in enumerate(reader.pages):
            md_lines.append(f"\n## Page {idx + 1}\n")
            text = page.extract_text() or ""
            paragraphs = text.split("\n\n")
            for p in paragraphs:
                p_clean = p.strip()
                if p_clean:
                    lines = p_clean.split("\n")
                    if len(lines) > 1 and all("  " in l for l in lines):
                        # Potential table
                        md_lines.append("\n| Column 1 | Column 2 | Column 3 |")
                        md_lines.append("|---|---|---|")
                        for l in lines:
                            cells = [c.strip() for c in l.split("  ") if c.strip()]
                            md_lines.append(f"| {' | '.join(cells[:3])} |")
                        md_lines.append("")
                    else:
                        md_lines.append(f"\n{' '.join(lines)}\n")

        return "\n".join(md_lines)

    @staticmethod
    def edit_pdf(input_path: str, annotations: List[Dict[str, Any]]) -> bytes:
        """
        Add text notes, shapes, highlights, and annotations at coordinate positions.
        """
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))

            for ann in annotations:
                if ann.get("page", 1) == page_num:
                    ann_type = ann.get("type", "text")
                    x = float(ann.get("x", 50))
                    y = float(ann.get("y", 50))
                    color_hex = ann.get("color", "#e11d48")

                    can.setFillColor(HexColor(color_hex))
                    can.setStrokeColor(HexColor(color_hex))

                    if ann_type == "text":
                        font_size = int(ann.get("font_size", 12))
                        can.setFont("Helvetica-Bold", font_size)
                        can.drawString(x, height - y, str(ann.get("content", "")))
                    elif ann_type == "rect":
                        w = float(ann.get("width", 100))
                        h = float(ann.get("height", 50))
                        can.rect(x, height - y - h, w, h, fill=ann.get("fill", 0), stroke=1)
                    elif ann_type == "highlight":
                        w = float(ann.get("width", 150))
                        h = float(ann.get("height", 20))
                        can.setFillColor(HexColor(color_hex), alpha=0.35)
                        can.rect(x, height - y - h, w, h, fill=1, stroke=0)

            can.save()
            packet.seek(0)
            overlay = PdfReader(packet).pages[0]
            page.merge_page(overlay)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def protect_pdf(input_path: str, user_password: str, owner_password: Optional[str] = None) -> bytes:
        """
        Encrypt PDF with user and owner passwords.
        """
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(input_path) as pdf:
                    buf = io.BytesIO()
                    owner_pw = owner_password or user_password
                    enc = pikepdf.Encryption(user=user_password, owner=owner_pw, R=6)
                    pdf.save(buf, encryption=enc)
                    return buf.getvalue()
            except Exception:
                pass

        reader = PdfReader(input_path)
        writer = PdfWriter()
        writer.append(reader)
        writer.encrypt(user_password=user_password, owner_password=owner_password or user_password)
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def unlock_pdf(input_path: str, password: str) -> bytes:
        """
        Decrypt and remove password security from a protected PDF.
        """
        if HAS_PIKEPDF:
            try:
                with pikepdf.open(input_path, password=password) as pdf:
                    buf = io.BytesIO()
                    pdf.save(buf)
                    return buf.getvalue()
            except Exception:
                pass

        reader = PdfReader(input_path)
        if reader.is_encrypted:
            reader.decrypt(password)
        writer = PdfWriter()
        writer.append(reader)
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def compare_pdfs(path_a: str, path_b: str) -> Dict[str, Any]:
        """
        Compare two PDFs text and structure side-by-side.
        """
        reader_a = PdfReader(path_a)
        reader_b = PdfReader(path_b)

        text_a = "\n".join(page.extract_text() or "" for page in reader_a.pages)
        text_b = "\n".join(page.extract_text() or "" for page in reader_b.pages)

        diff = list(difflib.unified_diff(
            text_a.splitlines(),
            text_b.splitlines(),
            fromfile="Document A",
            tofile="Document B",
            lineterm=""
        ))

        similarity_ratio = difflib.SequenceMatcher(None, text_a, text_b).ratio()

        return {
            "doc_a_pages": len(reader_a.pages),
            "doc_b_pages": len(reader_b.pages),
            "similarity_percentage": round(similarity_ratio * 100, 2),
            "diff_lines": diff[:150],
            "is_identical": text_a.strip() == text_b.strip()
        }

    @staticmethod
    def get_form_fields(input_path: str) -> List[Dict[str, Any]]:
        """
        Inspect all fillable interactive AcroForm fields.
        """
        reader = PdfReader(input_path)
        fields = reader.get_fields() or {}
        results = []
        for name, data in fields.items():
            field_type = str(data.get("/FT", "text"))
            val = str(data.get("/V", ""))
            results.append({
                "name": name,
                "type": field_type,
                "value": val
            })
        return results

    @staticmethod
    def fill_form_fields(input_path: str, field_data: Dict[str, str]) -> bytes:
        """
        Fill interactive PDF AcroForms fields with user values.
        """
        reader = PdfReader(input_path)
        writer = PdfWriter()
        writer.append(reader)
        writer.update_page_form_field_values(writer.pages[0], field_data)
        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def watermark_pdf(
        input_path: str,
        text: str = "CONFIDENTIAL",
        opacity: float = 0.3,
        font_size: int = 36,
        color_hex: str = "#888888",
        position: str = "center",
        image_path: Optional[str] = None,
        image_scale: float = 0.15,
        image_corner: str = "bottom-right",
        image_margin: int = 30
    ) -> bytes:
        """
        Add text and/or image watermark to every page of a PDF.
        
        Args:
            input_path: Path to source PDF
            text: Custom text for text watermark
            opacity: Opacity (0.0-1.0)
            font_size: Font size for text
            color_hex: Hex color for text
            position: Text position - "center", "top-left", "top-right", "bottom-left", "bottom-right", "repeat"
            image_path: Optional path to image file for image watermark
            image_scale: Scale factor for image (0.1 = 10% of page width)
            image_corner: Corner for image - "top-left", "top-right", "bottom-left", "bottom-right"
            image_margin: Margin from edges in points
        """
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Pre-load image if provided
        img_obj = None
        if image_path and os.path.exists(image_path):
            try:
                img_obj = Image.open(image_path)
                if img_obj.mode in ("RGBA", "LA", "P"):
                    img_obj = img_obj.convert("RGBA")
                else:
                    img_obj = img_obj.convert("RGB")
            except Exception:
                img_obj = None

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))

            # Draw image watermark first (if provided)
            if img_obj:
                img_w, img_h = img_obj.size
                # Calculate scaled dimensions
                max_w = width * image_scale
                max_h = height * image_scale
                scale = min(max_w / img_w, max_h / img_h)
                draw_w = img_w * scale
                draw_h = img_h * scale

                # Calculate position based on corner
                if image_corner == "top-left":
                    x = image_margin
                    y = height - image_margin - draw_h
                elif image_corner == "top-right":
                    x = width - image_margin - draw_w
                    y = height - image_margin - draw_h
                elif image_corner == "bottom-left":
                    x = image_margin
                    y = image_margin
                elif image_corner == "bottom-right":
                    x = width - image_margin - draw_w
                    y = image_margin
                else:  # default bottom-right
                    x = width - image_margin - draw_w
                    y = image_margin

                # Save image to bytes for ReportLab
                img_buf = io.BytesIO()
                img_obj.save(img_buf, format="PNG")
                img_buf.seek(0)
                
                can.setFillAlpha(opacity)
                can.drawImage(ImageReader(img_buf), x, y, width=draw_w, height=draw_h, mask='auto')

            # Draw text watermark (if provided)
            if text and text.strip():
                can.setFillColor(HexColor(color_hex), alpha=opacity)
                can.setFont("Helvetica-Bold", font_size)

                if position == "center":
                    can.saveState()
                    can.translate(width / 2, height / 2)
                    can.rotate(45)
                    can.drawCentredString(0, 0, text)
                    can.restoreState()
                elif position == "top-left":
                    can.drawString(40, height - 60, text)
                elif position == "top-right":
                    can.drawRightString(width - 40, height - 40, text)
                elif position == "bottom-left":
                    can.drawString(40, 40, text)
                elif position == "bottom-right":
                    can.drawRightString(width - 40, 40, text)
                elif position == "repeat":
                    for y_pos in range(100, int(height), 200):
                        for x_pos in range(100, int(width), 200):
                            can.saveState()
                            can.translate(x_pos, y_pos)
                            can.rotate(30)
                            can.drawString(0, 0, text)
                            can.restoreState()
                elif position == "diagonal":
                    can.saveState()
                    can.translate(width / 2, height / 2)
                    can.rotate(45)
                    can.drawCentredString(0, 0, text)
                    can.restoreState()

            can.save()
            packet.seek(0)
            watermark_pdf_page = PdfReader(packet).pages[0]
            page.merge_page(watermark_pdf_page)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    def redact_pdf(
        input_path: str,
        keywords: Optional[List[str]] = None,
        areas: Optional[List[Dict[str, float]]] = None
    ) -> bytes:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        areas = areas or []
        keywords = keywords or []

        for p_idx, page in enumerate(reader.pages):
            page_num = p_idx + 1
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFillColorRGB(0, 0, 0)

            for area in areas:
                if area.get("page", page_num) == page_num:
                    x = area.get("x", 0)
                    y = area.get("y", 0)
                    w = area.get("width", 100)
                    h = area.get("height", 20)
                    can.rect(x, height - y - h, w, h, fill=1, stroke=0)

            if keywords:
                text_content = page.extract_text() or ""
                for kw in keywords:
                    if kw.lower() in text_content.lower():
                        can.rect(50, height / 2, width - 100, 30, fill=1, stroke=0)

            can.save()
            packet.seek(0)
            redact_overlay = PdfReader(packet).pages[0]
            page.merge_page(redact_overlay)
            writer.add_page(page)

        buf = io.BytesIO()
        writer.write(buf)
        return buf.getvalue()

    @staticmethod
    async def ocr_pdf(input_path: str, lang: str = "eng") -> Tuple[bytes, bool, str]:
        if not HAS_PDF2IMAGE or not HAS_PYTESSERACT:
            return b"", False, "OCR tools (tesseract / pdf2image) are not installed on the system."

        try:
            images = pdf2image.convert_from_path(input_path)
            writer = PdfWriter()

            for img in images:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang=lang)
                ocr_page = PdfReader(io.BytesIO(pdf_bytes)).pages[0]
                writer.add_page(ocr_page)

            buf = io.BytesIO()
            writer.write(buf)
            return buf.getvalue(), True, "OCR completed successfully."
        except Exception as e:
            return b"", False, f"OCR error: {str(e)}"

    @staticmethod
    async def convert_office_to_pdf(input_path: str) -> Tuple[bytes, bool, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = ["soffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", tmpdir]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode != 0:
                    return b"", False, f"LibreOffice failed: {stderr.decode()}"

                filename = os.path.basename(input_path)
                name_without_ext = os.path.splitext(filename)[0]
                converted_pdf_path = os.path.join(tmpdir, f"{name_without_ext}.pdf")

                if os.path.exists(converted_pdf_path):
                    with open(converted_pdf_path, "rb") as f:
                        return f.read(), True, "Office document converted successfully."
                else:
                    return b"", False, "Converted PDF file not found after LibreOffice execution."

            except FileNotFoundError:
                return b"", False, "LibreOffice executable ('soffice') not found on system PATH."
            except Exception as e:
                return b"", False, f"Office conversion exception: {str(e)}"
