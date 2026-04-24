# Generic audit-trail recorder + reader.
# Keeps a unified timeline of material changes across controls, assessments, issues.

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from db import db
from models import User
from services.auth import get_current_user

logger = logging.getLogger(__name__)
api_router = APIRouter()


async def record_audit(
    entity_type: str,
    entity_id: str,
    action: str,
    actor_email: str,
    actor_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist an audit entry. Callers should be non-fatal: never raise to the
    request handler if audit writing fails — it must not block business logic."""
    try:
        await db.audit_log.insert_one({
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor_email": actor_email,
            "actor_role": actor_role,
            "details": details or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.warning("audit write failed for %s/%s: %s", entity_type, entity_id, e)


@api_router.get("/{entity_type}/{entity_id}")
async def get_audit_timeline(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return the audit trail for a single entity, most recent first."""
    events: List[Dict[str, Any]] = await db.audit_log.find(
        {"entity_type": entity_type, "entity_id": entity_id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(limit)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total": len(events),
        "events": events,
    }


@api_router.get("")
async def list_recent_audit(
    entity_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Stream of recent audit events across entities, useful for admins."""
    query: Dict[str, Any] = {}
    if entity_type:
        query["entity_type"] = entity_type
    events = await db.audit_log.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return {"total": len(events), "events": events}
