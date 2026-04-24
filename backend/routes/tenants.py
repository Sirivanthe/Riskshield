# Multi-Tenancy API Routes
# Tenant management endpoints

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.multi_tenancy import MultiTenancyService, get_tenant_service

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Request/Response Models
class CreateTenantRequest(BaseModel):
    tenant_id: str
    name: str
    display_name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    display_name: str
    database_name: str
    status: str
    created_at: str
    settings: Dict[str, Any]

class TenantStatsResponse(BaseModel):
    tenant_id: str
    collections: Dict[str, int]


@api_router.get("/")
async def list_tenants() -> List[TenantResponse]:
    """List all tenants."""
    try:
        service = get_tenant_service()
        tenants = await service.list_tenants()
        
        return [
            TenantResponse(
                id=t.id,
                name=t.name,
                display_name=t.display_name,
                database_name=t.database_name,
                status=t.status,
                created_at=t.created_at.isoformat(),
                settings=t.settings or {}
            )
            for t in tenants
        ]
        
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/", response_model=TenantResponse)
async def create_tenant(request: CreateTenantRequest):
    """
    Create a new tenant with isolated database.
    
    This creates:
    - A new MongoDB database for the tenant
    - Required collections with indexes
    - Tenant metadata in master database
    """
    try:
        service = get_tenant_service()
        
        tenant = await service.create_tenant(
            tenant_id=request.tenant_id,
            name=request.name,
            display_name=request.display_name,
            settings=request.settings
        )
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            display_name=tenant.display_name,
            database_name=tenant.database_name,
            status=tenant.status,
            created_at=tenant.created_at.isoformat(),
            settings=tenant.settings or {}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """Get tenant details."""
    try:
        service = get_tenant_service()
        tenant = await service.get_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            display_name=tenant.display_name,
            database_name=tenant.database_name,
            status=tenant.status,
            created_at=tenant.created_at.isoformat(),
            settings=tenant.settings or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(tenant_id: str):
    """Get statistics for a tenant."""
    try:
        service = get_tenant_service()
        stats = await service.get_tenant_stats(tenant_id)
        
        return TenantStatsResponse(**stats)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting tenant stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str):
    """Suspend a tenant (blocks access but preserves data)."""
    try:
        if tenant_id == "default":
            raise HTTPException(status_code=400, detail="Cannot suspend default tenant")
        
        service = get_tenant_service()
        success = await service.suspend_tenant(tenant_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {"message": f"Tenant {tenant_id} suspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suspending tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/{tenant_id}/activate")
async def activate_tenant(tenant_id: str):
    """Reactivate a suspended tenant."""
    try:
        service = get_tenant_service()
        success = await service.activate_tenant(tenant_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        return {"message": f"Tenant {tenant_id} activated successfully"}
        
    except Exception as e:
        logger.error(f"Error activating tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    hard_delete: bool = Query(default=False)
):
    """
    Delete a tenant.
    
    Args:
        tenant_id: Tenant to delete
        hard_delete: If True, drops the entire database (irreversible)
    """
    try:
        if tenant_id == "default":
            raise HTTPException(status_code=400, detail="Cannot delete default tenant")
        
        service = get_tenant_service()
        success = await service.delete_tenant(tenant_id, hard_delete)
        
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        action = "permanently deleted" if hard_delete else "marked as deleted"
        return {"message": f"Tenant {tenant_id} {action}"}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
