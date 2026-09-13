import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Document, VersionedOutput
from app.schemas import (
    VersionedOutputResponse, MergeRequest, SplitRequest,
    ReorderRotateRequest, CompressRequest, WatermarkRequest,
    RedactRequest, OCRRequest, ConvertOfficeRequest,
    RotatePDFRequest, CropPDFRequest, PageNumbersRequest,
    RepairPDFRequest, HTMLToPDFRequest, PDFToWordRequest,
    PDFToExcelRequest, PDFToPowerPointRequest, PDFToImagesRequest,
    PDFToMarkdownRequest, EditPDFRequest, ProtectPDFRequest,
    UnlockPDFRequest, ComparePDFsRequest, FillFormRequest
)
from app.services.storage_service import StorageService
from app.services.pdf_service import PDFService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/operations", tags=["operations"])

@router.get("/outputs", response_model=List[VersionedOutputResponse])
async def list_outputs(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(VersionedOutput).order_by(VersionedOutput.created_at.desc()))
    return res.scalars().all()

@router.delete("/outputs/stale")
async def purge_stale_outputs(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Remove versioned outputs whose files no longer exist on disk,
    and parent documents whose storage files are missing.
    """
    outputs_res = await db.execute(select(VersionedOutput))
    outputs = outputs_res.scalars().all()

    docs_res = await db.execute(select(Document))
    docs = docs_res.scalars().all()

    deleted_outputs = []
    deleted_docs = []

    # 1. Delete orphaned / missing versioned outputs
    for out in outputs:
        if not os.path.exists(out.storage_path):
            deleted_outputs.append(out)
            await db.delete(out)

    # 2. Delete documents whose files are missing
    for doc in docs:
        if not os.path.exists(doc.storage_path):
            deleted_docs.append(doc)
            await db.delete(doc)

    await db.commit()

    client_ip = request.client.host if request.client else "127.0.0.1"
    if deleted_outputs or deleted_docs:
        await AuditService.log_event(
            db=db,
            event_type="STALE_RECORDS_PURGED",
            client_ip=client_ip,
            details={
                "deleted_outputs": len(deleted_outputs),
                "deleted_documents": len(deleted_docs),
                "output_filenames": [o.filename for o in deleted_outputs],
                "document_filenames": [d.filename for d in deleted_docs],
            }
        )

    return {
        "message": f"Purged {len(deleted_outputs)} stale output(s) and {len(deleted_docs)} missing document(s).",
        "deleted_outputs": len(deleted_outputs),
        "deleted_documents": len(deleted_docs),
        "output_filenames": [o.filename for o in deleted_outputs],
        "document_filenames": [d.filename for d in deleted_docs],
    }

@router.get("/outputs/{output_id}/download")
async def download_output(output_id: str, db: AsyncSession = Depends(get_db)):
    out = await StorageService.get_output_by_id(db, output_id)
    if not out or not os.path.exists(out.storage_path):
        raise HTTPException(status_code=404, detail="Versioned output file not found.")
    
    media_type = "application/pdf"
    if out.filename.endswith(".docx"):
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif out.filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif out.filename.endswith(".pptx"):
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    elif out.filename.endswith(".zip"):
        media_type = "application/zip"
    elif out.filename.endswith(".md"):
        media_type = "text/markdown"

    return FileResponse(
        out.storage_path,
        media_type=media_type,
        filename=out.filename
    )

@router.post("/merge", response_model=VersionedOutputResponse)
async def merge_pdfs(request: Request, body: MergeRequest, db: AsyncSession = Depends(get_db)):
    if len(body.document_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 documents are required for merge.")

    paths = []
    for doc_id in body.document_ids:
        doc = await StorageService.get_document_by_id(db, doc_id)
        if not doc or not os.path.exists(doc.storage_path):
            raise HTTPException(status_code=404, detail=f"Document ID {doc_id} not found.")
        paths.append(doc.storage_path)

    merged_bytes = PDFService.merge_pdfs(paths)
    page_count = PDFService.get_page_count(paths[0])

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=body.document_ids,
        operation_type="merge",
        parameters={"merged_doc_count": len(body.document_ids)},
        output_content=merged_bytes,
        filename=body.output_filename or "merged.pdf",
        page_count=page_count
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_MERGED",
        document_id=body.document_ids[0],
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"parents": body.document_ids, "output_filename": output.filename}
    )

    return output

@router.post("/split", response_model=List[VersionedOutputResponse])
async def split_pdf(request: Request, body: SplitRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    ranges_str = body.ranges
    if not ranges_str:
        total_p = PDFService.get_page_count(doc.storage_path)
        n = body.pages_per_split or 1
        range_parts = []
        for start in range(1, total_p + 1, n):
            end = min(total_p, start + n - 1)
            range_parts.append(f"{start}-{end}" if start != end else f"{start}")
        ranges_str = ", ".join(range_parts)

    split_results = PDFService.split_pdf_by_range(doc.storage_path, ranges_str)
    outputs = []

    for fname, pdf_bytes in split_results:
        out = await StorageService.save_versioned_output(
            db=db,
            parent_document_ids=[doc.id],
            operation_type="split",
            parameters={"ranges": ranges_str},
            output_content=pdf_bytes,
            filename=fname
        )
        outputs.append(out)

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_SPLIT",
        document_id=doc.id,
        client_ip=client_ip,
        details={"ranges": ranges_str, "split_count": len(outputs)}
    )

    return outputs

@router.post("/reorder-rotate", response_model=VersionedOutputResponse)
async def reorder_rotate(request: Request, body: ReorderRotateRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    items = [item.model_dump() for item in body.pages]
    output_bytes = PDFService.reorder_rotate_pages(doc.storage_path, items)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="reorder_rotate",
        parameters={"page_count": len(items)},
        output_content=output_bytes,
        filename=f"reordered_{doc.filename}",
        page_count=len(items)
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_REORDERED",
        document_id=doc.id,
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"page_count": len(items)}
    )

    return output

@router.post("/rotate", response_model=VersionedOutputResponse)
async def rotate_pdf(request: Request, body: RotatePDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    rotated_bytes = PDFService.rotate_pdf(doc.storage_path, angle=body.angle, page_selection=body.page_selection)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="rotate",
        parameters={"angle": body.angle, "selection": body.page_selection},
        output_content=rotated_bytes,
        filename=f"rotated_{body.angle}deg_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/crop", response_model=VersionedOutputResponse)
async def crop_pdf(request: Request, body: CropPDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    cropped_bytes = PDFService.crop_pdf(
        doc.storage_path,
        top_pct=body.top_pct,
        bottom_pct=body.bottom_pct,
        left_pct=body.left_pct,
        right_pct=body.right_pct
    )

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="crop",
        parameters=body.model_dump(),
        output_content=cropped_bytes,
        filename=f"cropped_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/page-numbers", response_model=VersionedOutputResponse)
async def add_page_numbers(request: Request, body: PageNumbersRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    numbered_bytes = PDFService.add_page_numbers(
        doc.storage_path,
        format_str=body.format_str,
        position=body.position,
        font_size=body.font_size,
        start_number=body.start_number
    )

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="page_numbers",
        parameters=body.model_dump(),
        output_content=numbered_bytes,
        filename=f"numbered_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/repair", response_model=VersionedOutputResponse)
async def repair_pdf(request: Request, body: RepairPDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    repaired_bytes = PDFService.repair_pdf(doc.storage_path)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="repair",
        parameters={"repaired": True},
        output_content=repaired_bytes,
        filename=f"repaired_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/pdf-to-pdfa", response_model=VersionedOutputResponse)
async def pdf_to_pdfa(request: Request, body: RepairPDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    pdfa_bytes = PDFService.pdf_to_pdfa(doc.storage_path)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="pdf_to_pdfa",
        parameters={"format": "PDF/A-1b"},
        output_content=pdfa_bytes,
        filename=f"pdfa_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/html-to-pdf", response_model=VersionedOutputResponse)
async def html_to_pdf(request: Request, body: HTMLToPDFRequest, db: AsyncSession = Depends(get_db)):
    pdf_bytes = PDFService.html_to_pdf(body.html_content, title=body.title or "HTML Document")

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[],
        operation_type="html_to_pdf",
        parameters={"title": body.title},
        output_content=pdf_bytes,
        filename=f"html_converted_{body.title.replace(' ', '_').lower()}.pdf",
        page_count=1
    )

    return output

@router.post("/pdf-to-word", response_model=VersionedOutputResponse)
async def pdf_to_word(request: Request, body: PDFToWordRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    docx_bytes = PDFService.pdf_to_word(doc.storage_path)
    name_without_ext = os.path.splitext(doc.filename)[0]

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="pdf_to_word",
        parameters={"format": "docx"},
        output_content=docx_bytes,
        filename=f"{name_without_ext}.docx",
        page_count=doc.page_count
    )

    return output

@router.post("/pdf-to-excel", response_model=VersionedOutputResponse)
async def pdf_to_excel(request: Request, body: PDFToExcelRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    xlsx_bytes = PDFService.pdf_to_excel(doc.storage_path)
    name_without_ext = os.path.splitext(doc.filename)[0]

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="pdf_to_excel",
        parameters={"format": "xlsx"},
        output_content=xlsx_bytes,
        filename=f"{name_without_ext}.xlsx",
        page_count=doc.page_count
    )

    return output

@router.post("/pdf-to-powerpoint", response_model=VersionedOutputResponse)
async def pdf_to_powerpoint(request: Request, body: PDFToPowerPointRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    pptx_bytes = PDFService.pdf_to_powerpoint(doc.storage_path)
    name_without_ext = os.path.splitext(doc.filename)[0]

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="pdf_to_powerpoint",
        parameters={"format": "pptx"},
        output_content=pptx_bytes,
        filename=f"{name_without_ext}.pptx",
        page_count=doc.page_count
    )

    return output

@router.post("/pdf-to-images", response_model=VersionedOutputResponse)
async def pdf_to_images(request: Request, body: PDFToImagesRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    zip_bytes = PDFService.pdf_to_images_zip(doc.storage_path, img_format=body.format, dpi=body.dpi)
    name_without_ext = os.path.splitext(doc.filename)[0]

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="pdf_to_images",
        parameters={"format": body.format, "dpi": body.dpi},
        output_content=zip_bytes,
        filename=f"{name_without_ext}_images.zip",
        page_count=doc.page_count
    )

    return output

@router.post("/pdf-to-markdown", response_model=VersionedOutputResponse)
async def pdf_to_markdown(request: Request, body: PDFToMarkdownRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    md_str = PDFService.pdf_to_markdown(doc.storage_path)
    name_without_ext = os.path.splitext(doc.filename)[0]

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="pdf_to_markdown",
        parameters={"format": "md"},
        output_content=md_str.encode("utf-8"),
        filename=f"{name_without_ext}.md",
        page_count=doc.page_count
    )

    return output

@router.post("/edit", response_model=VersionedOutputResponse)
async def edit_pdf(request: Request, body: EditPDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    annotations = [ann.model_dump() for ann in body.annotations]
    edited_bytes = PDFService.edit_pdf(doc.storage_path, annotations)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="edit_pdf",
        parameters={"annotation_count": len(annotations)},
        output_content=edited_bytes,
        filename=f"annotated_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/protect", response_model=VersionedOutputResponse)
async def protect_pdf(request: Request, body: ProtectPDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    encrypted_bytes = PDFService.protect_pdf(doc.storage_path, user_password=body.password)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="protect_pdf",
        parameters={"encrypted": True},
        output_content=encrypted_bytes,
        filename=f"protected_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/unlock", response_model=VersionedOutputResponse)
async def unlock_pdf(request: Request, body: UnlockPDFRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        decrypted_bytes = PDFService.unlock_pdf(doc.storage_path, password=body.password)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to unlock PDF. Invalid password.")

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="unlock_pdf",
        parameters={"unlocked": True},
        output_content=decrypted_bytes,
        filename=f"unlocked_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/compare")
async def compare_pdfs(body: ComparePDFsRequest, db: AsyncSession = Depends(get_db)):
    doc_a = await StorageService.get_document_by_id(db, body.document_id_a)
    doc_b = await StorageService.get_document_by_id(db, body.document_id_b)
    if not doc_a or not doc_b or not os.path.exists(doc_a.storage_path) or not os.path.exists(doc_b.storage_path):
        raise HTTPException(status_code=404, detail="One or both documents not found.")

    res = PDFService.compare_pdfs(doc_a.storage_path, doc_b.storage_path)
    return res

@router.get("/forms/{document_id}")
async def get_forms(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")
    
    fields = PDFService.get_form_fields(doc.storage_path)
    return {"document_id": document_id, "fields": fields}

@router.post("/forms/fill", response_model=VersionedOutputResponse)
async def fill_forms(request: Request, body: FillFormRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    filled_bytes = PDFService.fill_form_fields(doc.storage_path, body.field_values)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="fill_forms",
        parameters=body.field_values,
        output_content=filled_bytes,
        filename=f"filled_{doc.filename}",
        page_count=doc.page_count
    )

    return output

@router.post("/compress", response_model=VersionedOutputResponse)
async def compress_pdf(request: Request, body: CompressRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    compressed_bytes = PDFService.compress_pdf(doc.storage_path, body.quality)

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="compress",
        parameters={"quality": body.quality, "original_size": doc.file_size, "compressed_size": len(compressed_bytes)},
        output_content=compressed_bytes,
        filename=f"compressed_{doc.filename}",
        page_count=doc.page_count
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_COMPRESSED",
        document_id=doc.id,
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"original_size": doc.file_size, "compressed_size": len(compressed_bytes)}
    )

    return output

@router.post("/watermark", response_model=VersionedOutputResponse)
async def watermark_pdf(request: Request, body: WatermarkRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    watermarked_bytes = PDFService.watermark_pdf(
        doc.storage_path,
        text=body.text or "CONFIDENTIAL",
        opacity=body.opacity,
        font_size=body.font_size,
        color_hex=body.color,
        position=body.position
    )

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="watermark",
        parameters={"text": body.text, "position": body.position, "opacity": body.opacity},
        output_content=watermarked_bytes,
        filename=f"watermarked_{doc.filename}",
        page_count=doc.page_count
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_WATERMARKED",
        document_id=doc.id,
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"text": body.text}
    )

    return output

@router.post("/redact", response_model=VersionedOutputResponse)
async def redact_pdf(request: Request, body: RedactRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    redacted_bytes = PDFService.redact_pdf(
        doc.storage_path,
        keywords=body.keywords,
        areas=body.areas
    )

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="redact",
        parameters={"keywords": body.keywords, "areas_count": len(body.areas or [])},
        output_content=redacted_bytes,
        filename=f"redacted_{doc.filename}",
        page_count=doc.page_count
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_REDACTED",
        document_id=doc.id,
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"keywords": body.keywords, "areas_count": len(body.areas or [])}
    )

    return output

@router.post("/ocr", response_model=VersionedOutputResponse)
async def ocr_pdf(request: Request, body: OCRRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    pdf_bytes, success, msg = await PDFService.ocr_pdf(doc.storage_path, lang=body.language)
    if not success:
        raise HTTPException(status_code=503, detail=f"OCR Service Unavailable: {msg}")

    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="ocr",
        parameters={"language": body.language},
        output_content=pdf_bytes,
        filename=f"ocr_{doc.filename}",
        page_count=doc.page_count
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="PDF_OCR_PROCESSED",
        document_id=doc.id,
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"language": body.language}
    )

    return output

@router.post("/convert-office", response_model=VersionedOutputResponse)
async def convert_office(request: Request, body: ConvertOfficeRequest, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    pdf_bytes, success, msg = await PDFService.convert_office_to_pdf(doc.storage_path)
    if not success:
        raise HTTPException(status_code=503, detail=f"LibreOffice Conversion Unavailable: {msg}")

    name_without_ext = os.path.splitext(doc.filename)[0]
    output = await StorageService.save_versioned_output(
        db=db,
        parent_document_ids=[doc.id],
        operation_type="convert_office",
        parameters={"original_filename": doc.filename},
        output_content=pdf_bytes,
        filename=f"{name_without_ext}.pdf"
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="OFFICE_CONVERTED",
        document_id=doc.id,
        output_id=output.id,
        document_hash=output.sha256,
        client_ip=client_ip,
        details={"original_filename": doc.filename}
    )

    return output
