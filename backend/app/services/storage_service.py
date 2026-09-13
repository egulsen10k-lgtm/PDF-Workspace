import os
import hashlib
import shutil
import json
import zipfile
import datetime
from typing import Tuple, List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import Document, VersionedOutput, AuditEvent, SignatureRequest, utc_now

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class StorageService:
    @staticmethod
    async def save_original_document(
        db: AsyncSession,
        filename: str,
        content: bytes,
        mime_type: str = "application/pdf"
    ) -> Document:
        file_hash = calculate_bytes_sha256(content)
        file_size = len(content)
        
        # Unique target filename using hash prefix to avoid clashes
        sanitized_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        storage_filename = f"{file_hash[:12]}_{sanitized_filename}"
        storage_path = os.path.join(settings.STORAGE_DIR, "originals", storage_filename)
        
        # Originals are IMMUTABLE: write file only if it doesn't already exist or overwrite cleanly
        with open(storage_path, "wb") as f:
            f.write(content)
            
        doc = Document(
            filename=sanitized_filename,
            original_filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            sha256=file_hash,
            storage_path=storage_path,
            is_original=True
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def save_versioned_output(
        db: AsyncSession,
        parent_document_ids: List[str],
        operation_type: str,
        parameters: dict,
        output_content: bytes,
        filename: str,
        page_count: int = 0
    ) -> VersionedOutput:
        file_hash = calculate_bytes_sha256(output_content)
        file_size = len(output_content)

        # Determine version number for parent
        version = 1
        if parent_document_ids:
            # Query existing version count
            query = select(VersionedOutput).where(VersionedOutput.parent_document_ids.contains(parent_document_ids[0]))
            existing = await db.execute(query)
            version = len(existing.scalars().all()) + 1

        sanitized_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        storage_filename = f"v{version}_{file_hash[:12]}_{sanitized_filename}"
        storage_path = os.path.join(settings.STORAGE_DIR, "outputs", storage_filename)

        with open(storage_path, "wb") as f:
            f.write(output_content)

        output = VersionedOutput(
            parent_document_ids=parent_document_ids,
            operation_type=operation_type,
            parameters=parameters,
            version=version,
            filename=sanitized_filename,
            file_size=file_size,
            sha256=file_hash,
            storage_path=storage_path,
            page_count=page_count
        )
        db.add(output)
        await db.commit()
        await db.refresh(output)
        return output

    @staticmethod
    async def get_document_by_id(db: AsyncSession, doc_id: str) -> Optional[Document]:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_output_by_id(db: AsyncSession, output_id: str) -> Optional[VersionedOutput]:
        result = await db.execute(select(VersionedOutput).where(VersionedOutput.id == output_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_export_zip(db: AsyncSession) -> str:
        """Create a full export ZIP of all local data, documents, versioned outputs, and audit logs."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"ilovepdf_export_{timestamp}.zip"
        export_path = os.path.join(settings.STORAGE_DIR, "backups", export_filename)

        docs = (await db.execute(select(Document))).scalars().all()
        outputs = (await db.execute(select(VersionedOutput))).scalars().all()
        audits = (await db.execute(select(AuditEvent))).scalars().all()
        signatures = (await db.execute(select(SignatureRequest))).scalars().all()

        metadata = {
            "export_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "documents_count": len(docs),
            "versioned_outputs_count": len(outputs),
            "audit_events_count": len(audits),
            "signatures_count": len(signatures),
            "documents": [
                {
                    "id": d.id, "filename": d.filename, "sha256": d.sha256,
                    "file_size": d.file_size, "page_count": d.page_count,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                } for d in docs
            ],
            "versioned_outputs": [
                {
                    "id": o.id, "parent_document_ids": o.parent_document_ids,
                    "operation_type": o.operation_type, "version": o.version,
                    "sha256": o.sha256, "filename": o.filename,
                    "created_at": o.created_at.isoformat() if o.created_at else None
                } for o in outputs
            ],
            "audit_events": [
                {
                    "id": a.id, "event_type": a.event_type, "document_id": a.document_id,
                    "output_id": a.output_id, "timestamp": a.timestamp.isoformat() if a.timestamp else None,
                    "document_hash": a.document_hash, "details": a.details
                } for a in audits
            ]
        }

        with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Write metadata json
            zipf.writestr("metadata_export.json", json.dumps(metadata, indent=2))
            
            # Write original files
            for doc in docs:
                if os.path.exists(doc.storage_path):
                    zipf.write(doc.storage_path, arcname=f"originals/{doc.id}_{doc.filename}")

            # Write output files
            for out in outputs:
                if os.path.exists(out.storage_path):
                    zipf.write(out.storage_path, arcname=f"outputs/v{out.version}_{out.id}_{out.filename}")

        return export_path

    @staticmethod
    async def cleanup_expired_files(db: AsyncSession) -> int:
        now = utc_now()
        deleted_count = 0
        
        # Documents
        docs_res = await db.execute(select(Document).where(Document.expires_at != None, Document.expires_at <= now))
        expired_docs = docs_res.scalars().all()
        for doc in expired_docs:
            if os.path.exists(doc.storage_path):
                try:
                    os.remove(doc.storage_path)
                except Exception:
                    pass
            await db.delete(doc)
            deleted_count += 1

        # Outputs
        outs_res = await db.execute(select(VersionedOutput).where(VersionedOutput.expires_at != None, VersionedOutput.expires_at <= now))
        expired_outs = outs_res.scalars().all()
        for out in expired_outs:
            if os.path.exists(out.storage_path):
                try:
                    os.remove(out.storage_path)
                except Exception:
                    pass
            await db.delete(out)
            deleted_count += 1

        await db.commit()
        return deleted_count
