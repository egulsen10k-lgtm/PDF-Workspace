import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.storage_service import StorageService
from app.services.audit_service import AuditService
from app.schemas import BackupResponse

router = APIRouter(prefix="/api/export", tags=["export"])

@router.post("/full-zip")
async def export_full_zip(request: Request, db: AsyncSession = Depends(get_db)):
    zip_path = await StorageService.create_export_zip(db)
    filename = os.path.basename(zip_path)
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuditService.log_event(
        db=db,
        event_type="DOCUMENT_EXPORTED",
        client_ip=client_ip,
        details={"backup_filename": filename}
    )

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=filename
    )

@router.post("/cleanup-expired")
async def cleanup_expired(db: AsyncSession = Depends(get_db)):
    deleted_count = await StorageService.cleanup_expired_files(db)
    return {"message": "Cleanup completed", "deleted_files_count": deleted_count}
