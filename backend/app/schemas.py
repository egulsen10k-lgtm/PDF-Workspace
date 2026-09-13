import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Any, Dict

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    sha256: str
    page_count: int
    is_original: bool
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None
    inspection_warnings: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

# Inspection Warning schema
class PDFInspectionResult(BaseModel):
    has_custom_fonts: bool = False
    fonts_list: List[str] = []
    has_interactive_forms: bool = False
    form_field_count: int = 0
    has_digital_signatures: bool = False
    signature_count: int = 0
    is_encrypted: bool = False
    is_password_protected: bool = False
    warnings: List[str] = []

# Versioned Output Schema
class VersionedOutputResponse(BaseModel):
    id: str
    parent_document_ids: List[str]
    operation_type: str
    parameters: Dict[str, Any]
    version: int
    filename: str
    file_size: int
    sha256: str
    page_count: int
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Operation Requests
class MergeRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=2, description="IDs of documents to merge in order")
    output_filename: Optional[str] = "merged.pdf"

class SplitRequest(BaseModel):
    document_id: str
    mode: str = Field("ranges", description="'ranges' (e.g. '1-3,4-5') or 'every_n' (e.g. n=2)")
    ranges: Optional[str] = None
    pages_per_split: Optional[int] = 1

class ReorderRotatePageItem(BaseModel):
    page_index: int
    rotation: int = 0

class ReorderRotateRequest(BaseModel):
    document_id: str
    pages: List[ReorderRotatePageItem]

class RotatePDFRequest(BaseModel):
    document_id: str
    angle: int = Field(90, description="90, 180, 270")
    page_selection: str = Field("all", description="'all', 'even', 'odd', or comma-separated pages '1,3,5'")

class CropPDFRequest(BaseModel):
    document_id: str
    top_pct: float = Field(0.0, ge=0, le=50)
    bottom_pct: float = Field(0.0, ge=0, le=50)
    left_pct: float = Field(0.0, ge=0, le=50)
    right_pct: float = Field(0.0, ge=0, le=50)

class PageNumbersRequest(BaseModel):
    document_id: str
    format_str: str = "Page {page} of {total}"
    position: str = "bottom-center"
    font_size: int = 10
    start_number: int = 1

class RepairPDFRequest(BaseModel):
    document_id: str

class PDFtoPDFARequest(BaseModel):
    document_id: str

class HTMLToPDFRequest(BaseModel):
    html_content: str
    title: Optional[str] = "Generated Document"

class ConvertOfficeRequest(BaseModel):
    document_id: str

class PDFToWordRequest(BaseModel):
    document_id: str

class PDFToExcelRequest(BaseModel):
    document_id: str

class PDFToPowerPointRequest(BaseModel):
    document_id: str

class PDFToImagesRequest(BaseModel):
    document_id: str
    format: str = "jpg"
    dpi: int = 150

class PDFToMarkdownRequest(BaseModel):
    document_id: str

class EditPDFAnnotationItem(BaseModel):
    type: str = "text" # text, rect, highlight
    page: int = 1
    x: float = 50
    y: float = 50
    width: Optional[float] = 100
    height: Optional[float] = 30
    content: Optional[str] = "Note"
    font_size: Optional[int] = 12
    color: Optional[str] = "#e11d48"

class EditPDFRequest(BaseModel):
    document_id: str
    annotations: List[EditPDFAnnotationItem]

class ProtectPDFRequest(BaseModel):
    document_id: str
    password: str = Field(..., min_length=1)

class UnlockPDFRequest(BaseModel):
    document_id: str
    password: str = Field(..., min_length=1)

class ComparePDFsRequest(BaseModel):
    document_id_a: str
    document_id_b: str

class FillFormRequest(BaseModel):
    document_id: str
    field_values: Dict[str, str]

class CompressRequest(BaseModel):
    document_id: str
    quality: str = Field("medium", description="low, medium, high compression")

class WatermarkRequest(BaseModel):
    document_id: str
    text: Optional[str] = "CONFIDENTIAL"
    opacity: float = Field(0.3, ge=0.05, le=1.0)
    font_size: int = Field(36, ge=10, le=120)
    color: str = Field("#888888", description="Hex color")
    position: str = Field("center", description="center, top-left, bottom-right, repeat, top-right, bottom-left, diagonal")
    image_base64: Optional[str] = Field(None, description="Optional base64 PNG/JPG for image watermark")
    image_scale: float = Field(0.15, ge=0.01, le=1.0)
    image_corner: str = Field("bottom-right", description="Corner for image watermark top-left, top-right, bottom-left, bottom-right")
    image_margin: int = Field(30, ge=0, le=200)
    pages: Optional[List[int]] = None

class RedactRequest(BaseModel):
    document_id: str
    keywords: Optional[List[str]] = []
    areas: Optional[List[Dict[str, float]]] = []

class OCRRequest(BaseModel):
    document_id: str
    language: str = Field("eng", description="eng, deu, tur, spa")

# Signature Schemas
class SignatureField(BaseModel):
    page: int
    x: float
    y: float
    width: float
    height: float
    type: str = "signature"
    label: Optional[str] = "Signature"

class CreateSignatureRequest(BaseModel):
    document_id: str
    signer_email: EmailStr
    signer_name: str
    fields: List[SignatureField]
    expires_in_days: Optional[int] = 30

class SignatureRequestResponse(BaseModel):
    id: str
    document_id: str
    signer_email: str
    signer_name: str
    access_token: str
    status: str
    fields: List[Dict[str, Any]]
    consent_given: bool
    consent_timestamp: Optional[datetime.datetime] = None
    signed_output_id: Optional[str] = None
    final_pdf_hash: Optional[str] = None
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SignerSubmitRequest(BaseModel):
    access_token: str
    consent_given: bool = Field(True, description="Must check consent box")
    consent_text: str = Field(..., description="The agreement consent text recorded")
    signature_data: str = Field(..., description="Base64 PNG data URL of signature image")
    typed_name: Optional[str] = None

# Audit Schemas
class AuditEventResponse(BaseModel):
    id: str
    event_type: str
    document_id: Optional[str] = None
    output_id: Optional[str] = None
    signature_request_id: Optional[str] = None
    timestamp: datetime.datetime
    document_hash: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

# Storage & Retention Schemas
class ExpiryUpdateRequest(BaseModel):
    days: Optional[int] = None

class BackupResponse(BaseModel):
    message: str
    backup_filename: str
    size_bytes: int
    created_at: datetime.datetime
