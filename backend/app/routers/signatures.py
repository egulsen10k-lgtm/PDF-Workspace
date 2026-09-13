from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import SignatureRequest
from app.schemas import CreateSignatureRequest, SignatureRequestResponse, SignerSubmitRequest, VersionedOutputResponse
from app.services.storage_service import StorageService
from app.services.signature_service import SignatureService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/signatures", tags=["signatures"])

@router.post("/request", response_model=SignatureRequestResponse)
async def create_signature_request(
    request: Request,
    body: CreateSignatureRequest,
    db: AsyncSession = Depends(get_db)
):
    doc = await StorageService.get_document_by_id(db, body.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    field_dicts = [f.model_dump() for f in body.fields]
    sig_req = await SignatureService.create_request(
        db=db,
        document_id=body.document_id,
        signer_email=body.signer_email,
        signer_name=body.signer_name,
        fields=field_dicts,
        expires_in_days=body.expires_in_days or 30
    )

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="SIGNATURE_REQUEST_CREATED",
        document_id=doc.id,
        signature_request_id=sig_req.id,
        document_hash=doc.sha256,
        client_ip=client_ip,
        details={
            "signer_email": body.signer_email,
            "signer_name": body.signer_name,
            "field_count": len(body.fields)
        }
    )

    return sig_req

@router.get("/request/{identifier}", response_model=SignatureRequestResponse)
async def get_signature_request(identifier: str, request: Request, db: AsyncSession = Depends(get_db)):
    sig_req = await SignatureService.get_by_token(db, identifier)
    if not sig_req:
        sig_req = await SignatureService.get_by_id(db, identifier)

    if not sig_req:
        raise HTTPException(status_code=404, detail="Signature request not found.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="SIGNATURE_VIEWED",
        document_id=sig_req.document_id,
        signature_request_id=sig_req.id,
        client_ip=client_ip,
        details={"signer_email": sig_req.signer_email}
    )

    return sig_req

@router.post("/submit", response_model=VersionedOutputResponse)
async def submit_signature(
    request: Request,
    body: SignerSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    sig_req = await SignatureService.get_by_token(db, body.access_token)
    if not sig_req:
        raise HTTPException(status_code=404, detail="Invalid signature token.")

    if sig_req.status == "signed":
        raise HTTPException(status_code=400, detail="Document has already been signed.")

    if not body.consent_given:
        raise HTTPException(status_code=400, detail="Consent must be explicitly given to complete e-signature.")

    doc = await StorageService.get_document_by_id(db, sig_req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Associated document not found.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown Signer Agent")

    await AuditService.log_event(
        db=db,
        event_type="SIGNATURE_CONSENT_RECORDED",
        document_id=doc.id,
        signature_request_id=sig_req.id,
        document_hash=doc.sha256,
        client_ip=client_ip,
        user_agent=user_agent,
        details={
            "consent_text": body.consent_text,
            "signer_name": sig_req.signer_name,
            "signer_email": sig_req.signer_email
        }
    )

    output, final_hash = await SignatureService.seal_and_complete_signature(
        db=db,
        req=sig_req,
        doc=doc,
        signature_data_url=body.signature_data,
        consent_text=body.consent_text,
        client_ip=client_ip,
        user_agent=user_agent
    )

    await AuditService.log_event(
        db=db,
        event_type="SIGNATURE_SEALED",
        document_id=doc.id,
        output_id=output.id,
        signature_request_id=sig_req.id,
        document_hash=final_hash,
        client_ip=client_ip,
        user_agent=user_agent,
        details={
            "final_sealed_hash": final_hash,
            "signed_output_filename": output.filename
        }
    )

    return output

@router.get("/list", response_model=List[SignatureRequestResponse])
async def list_signature_requests(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SignatureRequest).order_by(SignatureRequest.created_at.desc()))
    return res.scalars().all()
