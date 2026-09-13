import os
import pytest
import datetime
from sqlalchemy import select
from app.database import init_db, async_session_maker
from app.models import Document, VersionedOutput, SignatureRequest, AuditEvent, utc_now
from app.services.storage_service import StorageService
from app.services.signature_service import SignatureService
from app.services.audit_service import AuditService

@pytest.mark.asyncio
async def test_storage_service_edge_cases():
    await init_db()
    async with async_session_maker() as db:
        # 1. Save original document with special characters in filename
        doc = await StorageService.save_original_document(
            db=db,
            filename="test / file <name> : ?.pdf",
            content=b"%PDF-1.4 test content",
            mime_type="application/pdf"
        )
        assert doc.id is not None
        assert doc.sha256 is not None
        assert "/" not in doc.filename
        assert "<" not in doc.filename

        # 2. Save versioned output
        output = await StorageService.save_versioned_output(
            db=db,
            parent_document_ids=[doc.id],
            operation_type="compress",
            parameters={"quality": "high"},
            output_content=b"%PDF-1.4 compressed test",
            filename="compressed.pdf"
        )
        assert output.id is not None
        assert output.version == 1

        # Save second versioned output for same parent
        output2 = await StorageService.save_versioned_output(
            db=db,
            parent_document_ids=[doc.id],
            operation_type="watermark",
            parameters={"text": "WM"},
            output_content=b"%PDF-1.4 watermarked test",
            filename="watermarked.pdf"
        )
        assert output2.version == 2

        # 3. Create export zip
        export_zip_path = await StorageService.create_export_zip(db)
        assert os.path.exists(export_zip_path)
        assert export_zip_path.endswith(".zip")

        # 4. Cleanup expired files
        doc_exp = Document(
            filename="expired.pdf",
            original_filename="expired.pdf",
            mime_type="application/pdf",
            file_size=10,
            sha256="abc12345",
            storage_path=os.path.join("./data/storage/originals", "non_existent_file.pdf"),
            is_original=True,
            expires_at=utc_now() - datetime.timedelta(days=1)
        )
        db.add(doc_exp)
        await db.commit()

        deleted_count = await StorageService.cleanup_expired_files(db)
        assert deleted_count >= 1

@pytest.mark.asyncio
async def test_signature_service_edge_cases():
    await init_db()
    async with async_session_maker() as db:
        # Create base doc
        doc = await StorageService.save_original_document(
            db=db,
            filename="to_sign.pdf",
            content=b"%PDF-1.4 sample doc to sign",
            mime_type="application/pdf"
        )

        req = await SignatureService.create_request(
            db=db,
            document_id=doc.id,
            signer_email="bob@example.com",
            signer_name="Bob Jones",
            fields=[{"page": 1, "x": 10, "y": 10, "width": 20, "height": 10, "type": "signature"}],
            expires_in_days=7
        )
        assert req.access_token is not None

        # Fetch by token and id
        by_tok = await SignatureService.get_by_token(db, req.access_token)
        assert by_tok.id == req.id

        by_id = await SignatureService.get_by_id(db, req.id)
        assert by_id.access_token == req.access_token

        # Non-existent queries
        assert await SignatureService.get_by_token(db, "invalid_token_123") is None
        assert await SignatureService.get_by_id(db, "invalid_id_123") is None
