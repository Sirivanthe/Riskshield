# ServiceNow Integration API Routes
# Endpoints for GRC ticket management

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.servicenow_connector import (
    ServiceNowConnector, 
    ServiceNowTicket, 
    ServiceNowConfig,
    TicketPriority,
    create_risk_incident,
    create_control_deficiency_incident
)
from services.encryption import encrypt, decrypt
from db import db

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Initialize connector (will use mock mode if not configured)
connector = ServiceNowConnector()

# Request/Response Models
class CreateIncidentRequest(BaseModel):
    title: str
    description: str
    priority: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    category: str = "Risk Management"
    subcategory: str = "Control Deficiency"
    assignment_group: str = "IT Risk Management"
    risk_id: Optional[str] = None
    control_id: Optional[str] = None
    framework: Optional[str] = None

class RiskIncidentRequest(BaseModel):
    risk_title: str
    risk_description: str
    risk_id: str
    framework: str
    severity: str = "MEDIUM"
    assignment_group: str = "IT Risk Management"

class ControlDeficiencyRequest(BaseModel):
    control_name: str
    control_id: str
    deficiency: str
    framework: str
    effectiveness: str = "INEFFECTIVE"
    assignment_group: str = "IT Risk Management"

class TicketResponse(BaseModel):
    success: bool
    sys_id: Optional[str] = None
    number: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    mock: bool = False

class UpdateTicketRequest(BaseModel):
    state: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    work_notes: Optional[str] = None
    close_notes: Optional[str] = None


@api_router.get("/status")
async def get_servicenow_status():
    """Check ServiceNow integration status."""
    cfg = connector.config
    return {
        "configured": connector.is_configured,
        "mode": "live" if connector.is_configured else "mock",
        "mock_tickets_count": len(connector._mock_tickets) if hasattr(connector, '_mock_tickets') else 0,
        "instance_url": cfg.instance_url if cfg else None,
        "auth_type": cfg.auth_type if cfg else None,
    }


# ---- Configuration management (credentials or API token) ----

class ServiceNowConfigRequest(BaseModel):
    instance_url: str
    auth_type: str = "basic"  # "basic" or "token"
    username: Optional[str] = None
    password: Optional[str] = None
    api_token: Optional[str] = None
    api_version: Optional[str] = "v2"


def _safe_config(cfg: Optional[ServiceNowConfig]) -> Dict[str, Any]:
    if not cfg:
        return {
            "configured": False, "mode": "mock",
            "instance_url": None, "auth_type": None,
            "username": None, "password_set": False, "api_token_set": False,
        }
    return {
        "configured": connector.is_configured,
        "mode": "live" if connector.is_configured else "mock",
        "instance_url": cfg.instance_url,
        "auth_type": cfg.auth_type,
        "username": cfg.username or None,
        "password_set": bool(cfg.password),
        "api_token_set": bool(cfg.api_token),
        "api_token_last4": cfg.api_token[-4:] if cfg.api_token else None,
        "api_version": cfg.api_version,
    }


@api_router.get("/config")
async def get_config():
    """Return current ServiceNow configuration (secrets masked)."""
    return _safe_config(connector.config)


@api_router.put("/config")
async def save_config(request: ServiceNowConfigRequest):
    """Save ServiceNow credentials (Basic or API token). Persists to MongoDB."""
    auth_type = (request.auth_type or "basic").lower()
    if auth_type not in ("basic", "token"):
        raise HTTPException(status_code=400, detail="auth_type must be 'basic' or 'token'")

    if auth_type == "basic":
        if not request.username or not request.password:
            raise HTTPException(status_code=400, detail="username and password are required for basic auth")
    else:
        if not request.api_token:
            raise HTTPException(status_code=400, detail="api_token is required for token auth")

    if not request.instance_url:
        raise HTTPException(status_code=400, detail="instance_url is required")

    cfg = ServiceNowConfig(
        instance_url=request.instance_url.rstrip("/"),
        username=request.username or "",
        password=request.password or "",
        api_token=request.api_token or "",
        auth_type=auth_type,
        api_version=request.api_version or "v2",
    )
    connector.update_config(cfg)

    await db.integration_config.update_one(
        {"_id": "servicenow"},
        {"$set": {
            "instance_url": cfg.instance_url,
            "username": cfg.username,
            "password": encrypt(cfg.password) if cfg.password else "",
            "api_token": encrypt(cfg.api_token) if cfg.api_token else "",
            "auth_type": cfg.auth_type,
            "api_version": cfg.api_version,
        }},
        upsert=True,
    )
    return _safe_config(connector.config)


@api_router.delete("/config")
async def clear_config():
    """Clear saved credentials and return to mock mode."""
    connector.update_config(None)
    await db.integration_config.delete_one({"_id": "servicenow"})
    return _safe_config(None)


@api_router.post("/test")
async def test_connection():
    """Test connection against the current configuration."""
    return await connector.test_connection()


async def load_persisted_config() -> None:
    """Called at startup to rehydrate creds from MongoDB."""
    try:
        doc = await db.integration_config.find_one({"_id": "servicenow"}, {"_id": 0})
        if not doc:
            return
        cfg = ServiceNowConfig(
            instance_url=doc.get("instance_url", ""),
            username=doc.get("username", ""),
            password=decrypt(doc.get("password", "")) or "",
            api_token=decrypt(doc.get("api_token", "")) or "",
            auth_type=doc.get("auth_type", "basic"),
            api_version=doc.get("api_version", "v2"),
        )
        connector.update_config(cfg)
    except Exception as e:
        logger.warning(f"Could not load persisted ServiceNow config: {e}")


@api_router.post("/incidents", response_model=TicketResponse)
async def create_incident(request: CreateIncidentRequest):
    """
    Create a new incident in ServiceNow.
    
    If ServiceNow is not configured, creates a mock ticket for testing.
    """
    try:
        priority_map = {
            "CRITICAL": TicketPriority.CRITICAL,
            "HIGH": TicketPriority.HIGH,
            "MEDIUM": TicketPriority.MEDIUM,
            "LOW": TicketPriority.LOW
        }
        
        ticket = ServiceNowTicket(
            short_description=request.title,
            description=request.description,
            priority=priority_map.get(request.priority, TicketPriority.MEDIUM),
            category=request.category,
            subcategory=request.subcategory,
            assignment_group=request.assignment_group,
            u_risk_id=request.risk_id or "",
            u_control_id=request.control_id or "",
            u_framework=request.framework or ""
        )
        
        result = await connector.create_incident(ticket)
        
        return TicketResponse(
            success=result.get("success", False),
            sys_id=result.get("sys_id"),
            number=result.get("number"),
            state=result.get("state"),
            error=result.get("error"),
            mock=result.get("mock", False)
        )
        
    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/incidents/risk", response_model=TicketResponse)
async def create_risk_incident_endpoint(request: RiskIncidentRequest):
    """
    Create an incident for a risk finding.
    
    Pre-formatted for risk management workflows.
    """
    try:
        result = await create_risk_incident(
            connector=connector,
            risk_title=request.risk_title,
            risk_description=request.risk_description,
            risk_id=request.risk_id,
            framework=request.framework,
            severity=request.severity,
            assignment_group=request.assignment_group
        )
        
        return TicketResponse(
            success=result.get("success", False),
            sys_id=result.get("sys_id"),
            number=result.get("number"),
            state=result.get("state"),
            error=result.get("error"),
            mock=result.get("mock", False)
        )
        
    except Exception as e:
        logger.error(f"Error creating risk incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/incidents/control-deficiency", response_model=TicketResponse)
async def create_control_deficiency_endpoint(request: ControlDeficiencyRequest):
    """
    Create an incident for a control deficiency.
    
    Pre-formatted for control testing workflows.
    """
    try:
        result = await create_control_deficiency_incident(
            connector=connector,
            control_name=request.control_name,
            control_id=request.control_id,
            deficiency=request.deficiency,
            framework=request.framework,
            effectiveness=request.effectiveness,
            assignment_group=request.assignment_group
        )
        
        return TicketResponse(
            success=result.get("success", False),
            sys_id=result.get("sys_id"),
            number=result.get("number"),
            state=result.get("state"),
            error=result.get("error"),
            mock=result.get("mock", False)
        )
        
    except Exception as e:
        logger.error(f"Error creating control deficiency incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/incidents")
async def list_incidents(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """
    List incidents from ServiceNow.
    
    Returns mock tickets if ServiceNow is not configured.
    """
    try:
        query = None
        if status:
            query = f"state={status}"
        
        tickets = await connector.query_tickets("incident", query, limit)
        
        return {
            "total": len(tickets),
            "tickets": tickets,
            "mock": not connector.is_configured
        }
        
    except Exception as e:
        logger.error(f"Error listing incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/incidents/{sys_id}")
async def get_incident(sys_id: str):
    """Get incident details by sys_id."""
    try:
        ticket = await connector.get_ticket("incident", sys_id)
        
        if "error" in ticket:
            raise HTTPException(status_code=404, detail=ticket["error"])
        
        return {
            "ticket": ticket,
            "mock": not connector.is_configured
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.patch("/incidents/{sys_id}")
async def update_incident(sys_id: str, request: UpdateTicketRequest):
    """Update an existing incident."""
    try:
        updates = {}
        if request.state:
            updates["state"] = request.state
        if request.priority:
            updates["priority"] = request.priority
        if request.assigned_to:
            updates["assigned_to"] = request.assigned_to
        if request.work_notes:
            updates["work_notes"] = request.work_notes
        
        result = await connector.update_ticket("incident", sys_id, updates)
        
        return TicketResponse(
            success=result.get("success", False),
            sys_id=result.get("sys_id"),
            number=result.get("number"),
            state=result.get("state"),
            error=result.get("error"),
            mock=result.get("mock", False)
        )
        
    except Exception as e:
        logger.error(f"Error updating incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/incidents/{sys_id}/close")
async def close_incident(sys_id: str, resolution_notes: str = Query(...)):
    """Close an incident with resolution notes."""
    try:
        result = await connector.close_ticket("incident", sys_id, resolution_notes)
        
        return TicketResponse(
            success=result.get("success", False),
            sys_id=result.get("sys_id"),
            number=result.get("number"),
            state=result.get("state"),
            error=result.get("error"),
            mock=result.get("mock", False)
        )
        
    except Exception as e:
        logger.error(f"Error closing incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/bulk-create")
async def bulk_create_incidents(incidents: List[CreateIncidentRequest]):
    """Create multiple incidents at once."""
    results = []
    
    for incident_request in incidents:
        try:
            response = await create_incident(incident_request)
            results.append({
                "title": incident_request.title,
                "result": response.dict()
            })
        except Exception as e:
            results.append({
                "title": incident_request.title,
                "result": {"success": False, "error": str(e)}
            })
    
    successful = sum(1 for r in results if r["result"].get("success", False))
    
    return {
        "total": len(incidents),
        "successful": successful,
        "failed": len(incidents) - successful,
        "results": results
    }
