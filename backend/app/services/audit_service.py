from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditEvent, generate_uuid, utc_now

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        event_type: str,
        document_id: Optional[str] = None,
        output_id: Optional[str] = None,
        signature_request_id: Optional[str] = None,
        document_hash: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            document_id=document_id,
            output_id=output_id,
            signature_request_id=signature_request_id,
            document_hash=document_hash,
            client_ip=client_ip or "127.0.0.1",
            user_agent=user_agent or "Local-Client",
            details=details or {}
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event
