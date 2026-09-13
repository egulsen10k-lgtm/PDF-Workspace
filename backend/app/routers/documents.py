import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query, Response
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models import Document, VersionedOutput, utc_now
from app.schemas import DocumentResponse, VersionedOutputResponse, PDFInspectionResult, ExpiryUpdateRequest
from app.services.storage_service import StorageService
from app.services.pdf_service import PDFService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    mime = file.content_type or "application/pdf"
    doc = await StorageService.save_original_document(
        db=db,
        filename=file.filename or "uploaded.pdf",
        content=content,
        mime_type=mime
    )

    # Inspect PDF if it is a PDF file
    if doc.filename.lower().endswith(".pdf") or "pdf" in doc.mime_type.lower():
        inspection = PDFService.inspect_pdf(doc.storage_path)
        doc.inspection_warnings = inspection
        doc.page_count = PDFService.get_page_count(doc.storage_path)
        await db.commit()
        await db.refresh(doc)

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    await AuditService.log_event(
        db=db,
        event_type="DOCUMENT_UPLOADED",
        document_id=doc.id,
        document_hash=doc.sha256,
        client_ip=client_ip,
        user_agent=user_agent,
        details={"filename": doc.filename, "size": doc.file_size, "page_count": doc.page_count}
    )

    return doc

@router.get("", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()

@router.get("/version-tree")
async def get_version_tree(db: AsyncSession = Depends(get_db)):
    """
    Get all original documents with their versioned outputs nested underneath.
    """
    docs_res = await db.execute(select(Document).order_by(Document.created_at.desc()))
    documents = docs_res.scalars().all()

    outputs_res = await db.execute(select(VersionedOutput).order_by(VersionedOutput.created_at.asc()))
    outputs = outputs_res.scalars().all()

    tree = []
    matched_output_ids = set()

    for doc in documents:
        doc_versions = []
        for out in outputs:
            if doc.id in (out.parent_document_ids or []):
                doc_versions.append({
                    "id": out.id,
                    "version": out.version,
                    "filename": out.filename,
                    "operation_type": out.operation_type,
                    "parameters": out.parameters or {},
                    "file_size": out.file_size,
                    "sha256": out.sha256,
                    "page_count": out.page_count,
                    "created_at": out.created_at.isoformat() if out.created_at else None,
                    "parent_document_ids": out.parent_document_ids
                })
                matched_output_ids.add(out.id)

        tree.append({
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "mime_type": doc.mime_type,
                "file_size": doc.file_size,
                "sha256": doc.sha256,
                "page_count": doc.page_count,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "expires_at": doc.expires_at.isoformat() if doc.expires_at else None,
                "inspection_warnings": doc.inspection_warnings
            },
            "versions": doc_versions
        })

    # Add standalone/merged outputs that might not match single parent or generated independently
    standalone_versions = []
    for out in outputs:
        if out.id not in matched_output_ids:
            standalone_versions.append({
                "id": out.id,
                "version": out.version,
                "filename": out.filename,
                "operation_type": out.operation_type,
                "parameters": out.parameters or {},
                "file_size": out.file_size,
                "sha256": out.sha256,
                "page_count": out.page_count,
                "created_at": out.created_at.isoformat() if out.created_at else None,
                "parent_document_ids": out.parent_document_ids
            })

    return {
        "tree": tree,
        "standalone_outputs": standalone_versions
    }

@router.delete("/clear-all")
async def clear_all_documents(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Clear all user-added documents, versioned outputs, and files from local storage.
    """
    result = await db.execute(select(Document))
    docs = result.scalars().all()
    count = len(docs)

    for doc in docs:
        if os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except Exception:
                pass
        await db.delete(doc)

    # Also clear versioned outputs
    out_res = await db.execute(select(VersionedOutput))
    outputs = out_res.scalars().all()
    for out in outputs:
        if os.path.exists(out.storage_path):
            try:
                os.remove(out.storage_path)
            except Exception:
                pass
        await db.delete(out)

    await db.commit()

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="ALL_DOCUMENTS_CLEARED",
        client_ip=client_ip,
        details={"deleted_count": count, "deleted_outputs_count": len(outputs)}
    )

    return {"message": f"Successfully cleared {count} document(s) and {len(outputs)} output version(s).", "deleted_count": count}

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc

@router.get("/{doc_id}/download")
async def download_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, doc_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document or file not found.")
    return FileResponse(
        doc.storage_path,
        media_type=doc.mime_type,
        filename=doc.filename
    )

@router.get("/{doc_id}/preview")
async def get_page_preview(
    doc_id: str,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    doc = await StorageService.get_document_by_id(db, doc_id)
    if not doc or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="Document file not found.")
    
    png_bytes = PDFService.render_page_preview(doc.storage_path, page_number=page)
    return Response(content=png_bytes, media_type="image/png")

@router.delete("/{doc_id}")
async def delete_document(request: Request, doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await StorageService.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc_hash = doc.sha256
    filename = doc.filename
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    await db.delete(doc)
    await db.commit()

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="DOCUMENT_DELETED",
        document_id=doc_id,
        document_hash=doc_hash,
        client_ip=client_ip,
        details={"filename": filename}
    )

    return {"message": "Document deleted successfully."}

@router.patch("/{doc_id}/expiry", response_model=DocumentResponse)
async def update_expiry(
    doc_id: str,
    payload: ExpiryUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    doc = await StorageService.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if payload.days is not None:
        import datetime
        doc.expires_at = utc_now() + datetime.timedelta(days=payload.days)
    else:
        doc.expires_at = None

    await db.commit()
    await db.refresh(doc)
    return doc
