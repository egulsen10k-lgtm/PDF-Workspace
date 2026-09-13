import os
import io
import pytest
from httpx import AsyncClient, ASGITransport
from reportlab.pdfgen import canvas
from app.main import app
from app.database import init_db

def create_pdf_bytes() -> bytes:
    buf = io.BytesIO()
    can = canvas.Canvas(buf)
    can.drawString(100, 700, "Router Test PDF")
    can.showPage()
    can.save()
    return buf.getvalue()

@pytest.mark.asyncio
async def test_router_error_and_edge_cases():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Documents router edge cases
        # Upload empty file
        empty_res = await client.post("/api/documents/upload", files={"file": ("empty.pdf", b"", "application/pdf")})
        assert empty_res.status_code == 400

        # Non-existent document download
        no_doc_res = await client.get("/api/documents/00000000-0000-0000-0000-000000000000/download")
        assert no_doc_res.status_code == 404

        # Non-existent document delete
        no_del_res = await client.delete("/api/documents/00000000-0000-0000-0000-000000000000")
        assert no_del_res.status_code == 404

        # 2. Operations router edge cases
        # Merge with less than 2 document IDs
        merge_err = await client.post("/api/operations/merge", json={"document_ids": ["doc-1"]})
        assert merge_err.status_code == 422 # Pydantic min_length error or 400

        # Split with non-existent document ID
        split_err = await client.post("/api/operations/split", json={"document_id": "fake-id", "ranges": "1-2"})
        assert split_err.status_code == 404

        # Compress non-existent doc
        comp_err = await client.post("/api/operations/compress", json={"document_id": "fake-id", "quality": "medium"})
        assert comp_err.status_code == 404

        # 3. Signatures router edge cases
        # Invalid email address
        sig_err = await client.post("/api/signatures/request", json={
            "document_id": "fake-id",
            "signer_email": "not-an-email",
            "signer_name": "Test",
            "fields": []
        })
        assert sig_err.status_code == 422

        # Non-existent token retrieval
        get_sig_err = await client.get("/api/signatures/request/non_existent_token")
        assert get_sig_err.status_code == 404

        # Submit signature without consent
        sub_err = await client.post("/api/signatures/submit", json={
            "access_token": "invalid_token",
            "consent_given": False,
            "consent_text": "Consent",
            "signature_data": "data:image/png;base64,123"
        })
        assert sub_err.status_code == 404 # Token invalid
