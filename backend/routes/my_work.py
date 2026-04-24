# My Work — per-user aggregator used by the sidebar badge and /my-work page.
# Pulls open items across modules so LOD1/LOD2/Admin users have a single inbox.

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from db import db
from models import User, UserRole
from services.auth import get_current_user

logger = logging.getLogger(__name__)
api_router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_or_none(raw):
    if not raw:
        return None
    if isinstance(raw, datetime):
        # Make sure it's timezone-aware so we can compare against _now().
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


@api_router.get("")
async def my_work(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Aggregate pending work for the current user.

    Returns grouped buckets:
    - pending_approvals: controls / assessments awaiting my review (LOD2/Admin only)
    - overdue_issues: issues past due_date and not closed (everyone)
    - my_open_issues: issues owned by / assigned to me, not closed
    - running_assessments: my IN_PROGRESS assessments (so I can see the live orchestration)
    - sla_breaches: issues where we are within 48h of due_date (a nudge bucket)
    """
    role = current_user.role
    actor = current_user.email

    # --- Controls pending review (LOD2 / Admin) ---
    pending_controls: List[Dict[str, Any]] = []
    pending_assessments: List[Dict[str, Any]] = []
    if role in (UserRole.LOD2_USER, UserRole.ADMIN):
        pending_controls = await db.custom_controls.find(
            {"status": "PENDING_REVIEW"}, {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        pending_assessments = await db.assessments.find(
            {"status": {"$in": ["COMPLETED"]}, "summary.recommendations": {"$exists": True}},
            {"_id": 0, "id": 1, "name": 1, "system_name": 1, "business_unit": 1,
             "status": 1, "created_at": 1, "completed_at": 1, "summary.overall_score": 1},
        ).sort("completed_at", -1).to_list(25)

    # --- Overdue / near-due issues (everyone) ---
    now = _now()
    all_open_issues = await db.issues.find(
        {"status": {"$nin": ["CLOSED", "RESOLVED"]}},
        {"_id": 0},
    ).sort("due_date", 1).to_list(500)

    overdue_issues: List[Dict[str, Any]] = []
    sla_breaches: List[Dict[str, Any]] = []
    my_open_issues: List[Dict[str, Any]] = []
    for it in all_open_issues:
        due = _iso_or_none(it.get("due_date"))
        mine = (
            it.get("owner") == actor
            or it.get("assignee") == actor
            or it.get("creator_id") == current_user.id
        )
        if due:
            if due < now:
                overdue_issues.append(it)
            elif due - now <= timedelta(hours=48):
                sla_breaches.append(it)
        if mine:
            my_open_issues.append(it)

    # --- My running assessments (LOD1 sees theirs; LOD2/Admin see all) ---
    running_query: Dict[str, Any] = {"status": {"$in": ["PENDING", "IN_PROGRESS"]}}
    if role == UserRole.LOD1_USER:
        running_query["created_by"] = current_user.id
    running_assessments = await db.assessments.find(
        running_query,
        {"_id": 0, "id": 1, "name": 1, "system_name": 1, "business_unit": 1,
         "status": 1, "created_at": 1},
    ).sort("created_at", -1).to_list(25)

    counts = {
        "pending_approvals": len(pending_controls) + len(pending_assessments),
        "overdue_issues": len(overdue_issues),
        "sla_breaches": len(sla_breaches),
        "my_open_issues": len(my_open_issues),
        "running_assessments": len(running_assessments),
    }
    counts["total"] = sum(counts.values())

    return {
        "actor": {"email": actor, "role": role, "name": current_user.full_name},
        "counts": counts,
        "pending_controls": pending_controls[:25],
        "pending_assessments": pending_assessments[:25],
        "overdue_issues": overdue_issues[:25],
        "sla_breaches": sla_breaches[:25],
        "my_open_issues": my_open_issues[:25],
        "running_assessments": running_assessments[:25],
    }


@api_router.get("/count")
async def my_work_count(current_user: User = Depends(get_current_user)) -> Dict[str, int]:
    """Lightweight count-only endpoint used by the sidebar badge (polled often)."""
    data = await my_work(current_user)
    return {"total": data["counts"]["total"], **data["counts"]}
