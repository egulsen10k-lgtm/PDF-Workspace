from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models import AuditEvent
from app.schemas import AuditEventResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("/logs", response_model=List[AuditEventResponse])
async def get_audit_logs(
    document_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditEvent)
    if document_id:
        query = query.where(AuditEvent.document_id == document_id)
    if event_type:
        query = query.where(AuditEvent.event_type == event_type)

    query = query.order_by(desc(AuditEvent.timestamp)).limit(limit)
    res = await db.execute(query)
    return res.scalars().all()
