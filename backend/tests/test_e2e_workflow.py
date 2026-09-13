import os
import io
import pytest
from httpx import AsyncClient, ASGITransport
from reportlab.pdfgen import canvas
from app.main import app
from app.database import init_db

def create_sample_pdf_bytes(title: str = "Test Doc") -> bytes:
    buf = io.BytesIO()
    can = canvas.Canvas(buf)
    can.setFont("Helvetica", 14)
    can.drawString(100, 700, f"{title} Page 1")
    can.showPage()
    can.drawString(100, 700, f"{title} Page 2")
    can.showPage()
    can.save()
    return buf.getvalue()

@pytest.mark.asyncio
async def test_e2e_pdf_lifecycle_and_audit():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Upload Document 1
        pdf1_bytes = create_sample_pdf_bytes("Doc 1")
        res1 = await client.post(
            "/api/documents/upload",
            files={"file": ("doc1.pdf", pdf1_bytes, "application/pdf")}
        )
        assert res1.status_code == 200
        doc1_data = res1.json()
        assert doc1_data["filename"] == "doc1.pdf"
        assert doc1_data["sha256"] is not None
        doc1_id = doc1_data["id"]

        # 3. Upload Document 2
        pdf2_bytes = create_sample_pdf_bytes("Doc 2")
        res2 = await client.post(
            "/api/documents/upload",
            files={"file": ("doc2.pdf", pdf2_bytes, "application/pdf")}
        )
        assert res2.status_code == 200
        doc2_id = res2.json()["id"]

        # 4. Merge Documents
        merge_res = await client.post(
            "/api/operations/merge",
            json={"document_ids": [doc1_id, doc2_id], "output_filename": "merged_test.pdf"}
        )
        assert merge_res.status_code == 200
        merged_data = merge_res.json()
        assert merged_data["operation_type"] == "merge"
        assert merged_data["filename"] == "merged_test.pdf"

        # 5. Watermark Document 1
        wm_res = await client.post(
            "/api/operations/watermark",
            json={
                "document_id": doc1_id,
                "text": "PRIVATE USE ONLY",
                "opacity": 0.5,
                "position": "center"
            }
        )
        assert wm_res.status_code == 200

        # 6. Create Signature Request for Document 1
        sig_req_res = await client.post(
            "/api/signatures/request",
            json={
                "document_id": doc1_id,
                "signer_email": "alice@example.com",
                "signer_name": "Alice Smith",
                "fields": [
                    {"page": 1, "x": 10, "y": 70, "width": 30, "height": 10, "type": "signature"}
                ]
            }
        )
        assert sig_req_res.status_code == 200
        sig_req_data = sig_req_res.json()
        token = sig_req_data["access_token"]
        assert sig_req_data["status"] == "pending"

        # 7. Signer submits consent & signature
        dummy_sig_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        submit_res = await client.post(
            "/api/signatures/submit",
            json={
                "access_token": token,
                "consent_given": True,
                "consent_text": "I hereby consent to sign this document electronically.",
                "signature_data": dummy_sig_png,
                "typed_name": "Alice Smith"
            }
        )
        assert submit_res.status_code == 200
        sealed_output = submit_res.json()
        assert sealed_output["operation_type"] == "sign"

        # 8. Verify Audit Event Logs
        audit_res = await client.get("/api/audit/logs")
        assert audit_res.status_code == 200
        logs = audit_res.json()
        assert len(logs) >= 5
        event_types = [log["event_type"] for log in logs]
        assert "DOCUMENT_UPLOADED" in event_types
        assert "PDF_MERGED" in event_types
        assert "SIGNATURE_SEALED" in event_types

        # 9. Test Full Data Export ZIP
        export_res = await client.post("/api/export/full-zip")
        assert export_res.status_code == 200
        assert export_res.headers["content-type"] == "application/zip"
