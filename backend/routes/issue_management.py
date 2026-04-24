# Issue Management API Routes
# Full issue lifecycle with linking and ServiceNow integration

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.issue_management import (
    IssueManagementService, IssueStatus, IssuePriority, 
    IssueType, IssueSource
)

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Request/Response Models
class CreateIssueRequest(BaseModel):
    title: str
    description: str
    issue_type: str
    severity: str
    priority: str
    source: str = "MANUAL"
    owner: Optional[str] = None
    source_id: Optional[str] = None
    source_risk_id: Optional[str] = None
    source_control_id: Optional[str] = None
    app_name: Optional[str] = None
    business_unit: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = []
    
class UpdateIssueRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None

class AddCommentRequest(BaseModel):
    text: str
    is_internal: bool = False

class ResolveIssueRequest(BaseModel):
    resolution: str
    root_cause: str
    lessons_learned: Optional[str] = None

class LinkIssueRequest(BaseModel):
    target_id: str
    link_type: str  # assessment, control_test, remediation, issue


@api_router.post("/")
async def create_issue(
    request: CreateIssueRequest,
    creator_id: str = Query(...),
    creator_name: str = Query(...)
):
    """Create a new issue."""
    try:
        service = IssueManagementService()
        
        issue = await service.create_issue(
            title=request.title,
            description=request.description,
            issue_type=request.issue_type,
            severity=request.severity,
            priority=request.priority,
            source=request.source,
            creator_id=creator_id,
            creator_name=creator_name,
            owner=request.owner,
            source_id=request.source_id,
            source_risk_id=request.source_risk_id,
            source_control_id=request.source_control_id,
            app_name=request.app_name,
            business_unit=request.business_unit,
            due_date=request.due_date,
            tags=request.tags
        )
        
        return issue
        
    except Exception as e:
        logger.error(f"Error creating issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/")
async def list_issues(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    issue_type: Optional[str] = None,
    source: Optional[str] = None,
    owner: Optional[str] = None,
    app_name: Optional[str] = None,
    source_id: Optional[str] = None,
    overdue_only: bool = False,
    limit: int = Query(default=100, le=500)
):
    """List issues with filters."""
    try:
        service = IssueManagementService()
        
        issues = await service.list_issues(
            status=status,
            priority=priority,
            issue_type=issue_type,
            source=source,
            owner=owner,
            app_name=app_name,
            source_id=source_id,
            overdue_only=overdue_only,
            limit=limit
        )
        
        return {"total": len(issues), "issues": issues}
        
    except Exception as e:
        logger.error(f"Error listing issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/statistics")
async def get_statistics():
    """Get issue statistics for dashboard."""
    try:
        service = IssueManagementService()
        stats = await service.get_issue_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/overdue")
async def get_overdue_issues():
    """Get all overdue issues."""
    try:
        service = IssueManagementService()
        issues = await service.get_overdue_issues()
        return {"total": len(issues), "issues": issues}
    except Exception as e:
        logger.error(f"Error getting overdue issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/by-assessment/{assessment_id}")
async def get_issues_by_assessment(assessment_id: str):
    """Get all issues linked to an assessment."""
    try:
        service = IssueManagementService()
        issues = await service.get_issues_by_assessment(assessment_id)
        return {"total": len(issues), "issues": issues}
    except Exception as e:
        logger.error(f"Error getting issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/by-control-test/{control_test_id}")
async def get_issues_by_control_test(control_test_id: str):
    """Get all issues linked to a control test."""
    try:
        service = IssueManagementService()
        issues = await service.get_issues_by_control_test(control_test_id)
        return {"total": len(issues), "issues": issues}
    except Exception as e:
        logger.error(f"Error getting issues: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/{issue_id}")
async def get_issue(issue_id: str):
    """Get issue details with full history."""
    try:
        service = IssueManagementService()
        issue = await service.get_issue(issue_id)
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        return issue
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/{issue_id}")
async def update_issue(
    issue_id: str,
    request: UpdateIssueRequest,
    user_id: str = Query(...),
    user_name: str = Query(...)
):
    """Update an issue with history tracking."""
    try:
        service = IssueManagementService()
        
        updates = request.dict(exclude_none=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        issue = await service.update_issue(issue_id, updates, user_id, user_name)
        return issue
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{issue_id}/comments")
async def add_comment(
    issue_id: str,
    request: AddCommentRequest,
    user_id: str = Query(...),
    user_name: str = Query(...)
):
    """Add a comment to an issue."""
    try:
        service = IssueManagementService()
        
        issue = await service.add_comment(
            issue_id,
            request.text,
            user_id,
            user_name,
            request.is_internal
        )
        
        return issue
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{issue_id}/resolve")
async def resolve_issue(
    issue_id: str,
    request: ResolveIssueRequest,
    user_id: str = Query(...),
    user_name: str = Query(...)
):
    """Resolve an issue with documentation."""
    try:
        service = IssueManagementService()
        
        issue = await service.resolve_issue(
            issue_id,
            request.resolution,
            request.root_cause,
            request.lessons_learned or "",
            user_id,
            user_name
        )
        
        return issue
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{issue_id}/close")
async def close_issue(
    issue_id: str,
    user_id: str = Query(...),
    user_name: str = Query(...),
    close_reason: Optional[str] = None
):
    """Close a resolved issue."""
    try:
        service = IssueManagementService()
        issue = await service.close_issue(issue_id, user_id, user_name, close_reason)
        return issue
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error closing issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{issue_id}/link")
async def link_issue(
    issue_id: str,
    request: LinkIssueRequest,
    user_id: str = Query(...),
    user_name: str = Query(...)
):
    """Link an issue to another entity."""
    try:
        service = IssueManagementService()
        
        if request.link_type == "assessment":
            issue = await service.link_to_assessment(
                issue_id, request.target_id, user_id, user_name
            )
        elif request.link_type == "control_test":
            issue = await service.link_to_control_test(
                issue_id, request.target_id, user_id, user_name
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid link type: {request.link_type}")
        
        return issue
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{issue_id}/sync-servicenow")
async def sync_to_servicenow(
    issue_id: str,
    user_id: str = Query(...),
    user_name: str = Query(...)
):
    """Sync issue to ServiceNow."""
    try:
        service = IssueManagementService()
        result = await service.sync_to_servicenow(issue_id, user_id, user_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error syncing to ServiceNow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/enums/types")
async def get_issue_types():
    """Get available issue types."""
    return {
        "types": [
            {"id": t.value, "name": t.value.replace("_", " ").title()}
            for t in IssueType
        ]
    }


@api_router.get("/enums/statuses")
async def get_issue_statuses():
    """Get available issue statuses."""
    return {
        "statuses": [
            {"id": s.value, "name": s.value.replace("_", " ").title()}
            for s in IssueStatus
        ]
    }


@api_router.get("/enums/priorities")
async def get_issue_priorities():
    """Get available issue priorities."""
    return {
        "priorities": [
            {"id": "P1", "name": "P1 - Critical", "sla_response_hours": 1, "sla_resolution_hours": 24},
            {"id": "P2", "name": "P2 - High", "sla_response_hours": 4, "sla_resolution_hours": 72},
            {"id": "P3", "name": "P3 - Medium", "sla_response_hours": 24, "sla_resolution_hours": 168},
            {"id": "P4", "name": "P4 - Low", "sla_response_hours": 48, "sla_resolution_hours": 720}
        ]
    }


@api_router.get("/enums/sources")
async def get_issue_sources():
    """Get available issue sources."""
    return {
        "sources": [
            {"id": s.value, "name": s.value.replace("_", " ").title()}
            for s in IssueSource
        ]
    }
