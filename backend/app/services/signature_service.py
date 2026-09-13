import os
import io
import base64
import secrets
import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image

from app.models import SignatureRequest, Document, VersionedOutput, generate_uuid, utc_now
from app.services.storage_service import StorageService, calculate_bytes_sha256

class SignatureService:
    @staticmethod
    async def create_request(
        db: AsyncSession,
        document_id: str,
        signer_email: str,
        signer_name: str,
        fields: List[Dict[str, Any]],
        expires_in_days: int = 30
    ) -> SignatureRequest:
        token = secrets.token_urlsafe(32)
        expires_at = utc_now() + datetime.timedelta(days=expires_in_days)

        req = SignatureRequest(
            document_id=document_id,
            signer_email=signer_email,
            signer_name=signer_name,
            access_token=token,
            status="pending",
            fields=fields,
            expires_at=expires_at
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def get_by_token(db: AsyncSession, token: str) -> Optional[SignatureRequest]:
        result = await db.execute(select(SignatureRequest).where(SignatureRequest.access_token == token))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, req_id: str) -> Optional[SignatureRequest]:
        result = await db.execute(select(SignatureRequest).where(SignatureRequest.id == req_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def seal_and_complete_signature(
        db: AsyncSession,
        req: SignatureRequest,
        doc: Document,
        signature_data_url: str,
        consent_text: str,
        client_ip: str,
        user_agent: str
    ) -> Tuple[VersionedOutput, str]:
        """
        Record consent, render signature onto PDF pages, append seal certificate page, seal final PDF hash.
        """
        now = utc_now()
        req.consent_given = True
        req.consent_timestamp = now
        req.consent_ip = client_ip
        req.consent_user_agent = user_agent
        req.signature_data = signature_data_url
        req.status = "signed"

        # Read base PDF
        reader = PdfReader(doc.storage_path)
        writer = PdfWriter()

        # Extract base64 PNG signature
        sig_bytes = b""
        if "," in signature_data_url:
            sig_bytes = base64.b64decode(signature_data_url.split(",", 1)[1])
        else:
            sig_bytes = base64.b64decode(signature_data_url)

        sig_img = Image.open(io.BytesIO(sig_bytes))

        # Render overlays onto pages with signature fields
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            # Filter fields for this page
            page_fields = [f for f in req.fields if f.get("page") == page_num]

            if page_fields:
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=(width, height))

                for f in page_fields:
                    x_pct = f.get("x", 10)
                    y_pct = f.get("y", 10)
                    w_pct = f.get("width", 25)
                    h_pct = f.get("height", 10)

                    x = (x_pct / 100.0) * width if x_pct <= 100 else x_pct
                    y = (y_pct / 100.0) * height if y_pct <= 100 else y_pct
                    w = (w_pct / 100.0) * width if w_pct <= 100 else w_pct
                    h = (h_pct / 100.0) * height if h_pct <= 100 else h_pct

                    ry = height - y - h

                    ftype = f.get("type", "signature")
                    if ftype == "signature":
                        img_reader = ImageReader(sig_img)
                        can.drawImage(
                            img_reader,
                            x, ry, width=w, height=h,
                            mask='auto'
                        )
                    elif ftype == "date":
                        can.setFont("Helvetica", 10)
                        can.setFillColor(HexColor("#333333"))
                        can.drawString(x, ry + 5, f"Signed: {now.strftime('%Y-%m-%d %H:%M UTC')}")
                    elif ftype == "text":
                        can.setFont("Helvetica", 10)
                        can.setFillColor(HexColor("#333333"))
                        can.drawString(x, ry + 5, req.signer_name)

                can.save()
                packet.seek(0)
                field_overlay = PdfReader(packet).pages[0]
                page.merge_page(field_overlay)

            writer.add_page(page)

        # Build Audit Trail & Seal Certificate Page
        cert_packet = io.BytesIO()
        cert_width, cert_height = 595.27, 841.89 # A4
        can = canvas.Canvas(cert_packet, pagesize=(cert_width, cert_height))
        
        # Header banner
        can.setFillColor(HexColor("#1e293b"))
        can.rect(0, cert_height - 100, cert_width, 100, fill=1, stroke=0)
        can.setFillColor(HexColor("#ffffff"))
        can.setFont("Helvetica-Bold", 20)
        can.drawString(40, cert_height - 50, "ELECTRONIC SIGNATURE AUDIT CERTIFICATE")
        can.setFont("Helvetica", 10)
        can.drawString(40, cert_height - 75, "Self-Hosted Simple e-Sign Document Audit Trail")

        # Body details
        can.setFillColor(HexColor("#0f172a"))
        can.setFont("Helvetica-Bold", 12)
        y = cert_height - 140

        items = [
            ("Document Name:", doc.filename),
            ("Original Document Hash (SHA-256):", doc.sha256),
            ("Signer Name:", req.signer_name),
            ("Signer Email:", req.signer_email),
            ("Consent Timestamp:", now.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("Signer IP Address:", client_ip),
            ("Signer User-Agent:", user_agent[:60] if user_agent else "Unknown"),
            ("Access Token ID:", req.access_token[:16] + "..."),
            ("Recorded Consent Statement:", f'"{consent_text[:80]}..."')
        ]

        for label, val in items:
            can.setFont("Helvetica-Bold", 10)
            can.drawString(40, y, label)
            can.setFont("Helvetica", 10)
            can.drawString(220, y, str(val))
            y -= 24

        # Low-stakes warning notice
        y -= 20
        can.setFillColor(HexColor("#ef4444"))
        can.rect(40, y - 50, cert_width - 80, 60, fill=1, stroke=0)
        can.setFillColor(HexColor("#ffffff"))
        can.setFont("Helvetica-Bold", 10)
        can.drawString(50, y - 20, "NOTICE: FOR PERSONAL & LOW-STAKES USE ONLY")
        can.setFont("Helvetica", 9)
        can.drawString(50, y - 38, "This electronic signature record is generated locally. It does not constitute a Qualified Electronic Signature (QES)")
        can.drawString(50, y - 48, "under eIDAS or eSIGN regulations, and contains no government identity verification.")

        can.save()
        cert_packet.seek(0)
        cert_page = PdfReader(cert_packet).pages[0]
        writer.add_page(cert_page)

        # Write output PDF
        signed_buf = io.BytesIO()
        writer.write(signed_buf)
        signed_bytes = signed_buf.getvalue()

        # Compute final sealed PDF hash
        final_hash = calculate_bytes_sha256(signed_bytes)
        req.final_pdf_hash = final_hash

        # Save versioned output
        output = await StorageService.save_versioned_output(
            db=db,
            parent_document_ids=[doc.id],
            operation_type="sign",
            parameters={
                "signature_request_id": req.id,
                "signer_email": req.signer_email,
                "consent_timestamp": now.isoformat(),
                "final_hash": final_hash
            },
            output_content=signed_bytes,
            filename=f"signed_{doc.filename}",
            page_count=len(writer.pages)
        )

        req.signed_output_id = output.id
        await db.commit()

        return output, final_hash
