import uuid
import datetime
from typing import Optional, List, Any
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    is_original: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Inspection flags / warnings JSON
    inspection_warnings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    signature_requests = relationship("SignatureRequest", back_populates="document", cascade="all, delete-orphan")


class VersionedOutput(Base):
    __tablename__ = "versioned_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    parent_document_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False) # list of document IDs
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False) # merge, split, compress, watermark, redact, ocr, convert, sign, etc.
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SignatureRequest(Base):
    __tablename__ = "signature_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    signer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    signer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending") # pending, viewed, signed, rejected
    fields: Mapped[List[dict]] = mapped_column(JSON, default=list) # [{page: 1, x: 100, y: 200, width: 150, height: 50, type: 'signature'|'date'|'text'}]
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_ip: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    consent_user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    signature_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Data URL (base64 PNG) of signature image
    signed_output_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    final_pdf_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    document = relationship("Document", back_populates="signature_requests")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    output_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    signature_request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    document_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
