# Multi-Tenancy Service
# Database-per-tenant architecture for complete data isolation

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class Tenant:
    """Represents a tenant in the system."""
    id: str
    name: str
    display_name: str
    database_name: str
    created_at: datetime
    status: str = "active"  # active, suspended, deleted
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}

class MultiTenancyService:
    """
    Multi-tenancy service implementing database-per-tenant architecture.
    
    Features:
    - Complete data isolation per tenant
    - Tenant-specific database connections
    - Tenant management (create, suspend, delete)
    - Context-aware database selection
    """
    
    _instance = None
    _tenants: Dict[str, Tenant] = {}
    _db_clients: Dict[str, AsyncIOMotorClient] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.default_db_name = os.environ.get('DB_NAME', 'riskshield')
        self._master_client = None
        self._initialized = True
        
        # Initialize default tenant
        self._tenants["default"] = Tenant(
            id="default",
            name="default",
            display_name="Default Tenant",
            database_name=self.default_db_name,
            created_at=datetime.now(timezone.utc)
        )
    
    async def get_master_client(self) -> AsyncIOMotorClient:
        """Get the master MongoDB client."""
        if not self._master_client:
            self._master_client = AsyncIOMotorClient(self.mongo_url)
        return self._master_client
    
    async def get_tenant_db(self, tenant_id: str):
        """Get database connection for a specific tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")
        
        if tenant.status != "active":
            raise ValueError(f"Tenant is not active: {tenant_id}")
        
        client = await self.get_master_client()
        return client[tenant.database_name]
    
    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        display_name: str = None,
        settings: Dict[str, Any] = None
    ) -> Tenant:
        """
        Create a new tenant with isolated database.
        
        Args:
            tenant_id: Unique tenant identifier
            name: Tenant name (used for database naming)
            display_name: Human-readable name
            settings: Tenant-specific settings
        """
        if tenant_id in self._tenants:
            raise ValueError(f"Tenant already exists: {tenant_id}")
        
        # Create database name based on tenant
        database_name = f"riskshield_{name.lower().replace(' ', '_')}"
        
        tenant = Tenant(
            id=tenant_id,
            name=name,
            display_name=display_name or name,
            database_name=database_name,
            created_at=datetime.now(timezone.utc),
            settings=settings or {}
        )
        
        # Initialize tenant database with required collections
        await self._initialize_tenant_database(tenant)
        
        self._tenants[tenant_id] = tenant
        
        # Store tenant info in master database
        master_client = await self.get_master_client()
        master_db = master_client[self.default_db_name]
        
        await master_db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {
                "id": tenant.id,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "database_name": tenant.database_name,
                "created_at": tenant.created_at.isoformat(),
                "status": tenant.status,
                "settings": tenant.settings
            }},
            upsert=True
        )
        
        logger.info(f"Created tenant: {tenant_id} with database: {database_name}")
        return tenant
    
    async def _initialize_tenant_database(self, tenant: Tenant):
        """Initialize collections and indexes for a new tenant."""
        db = (await self.get_master_client())[tenant.database_name]
        
        # Create required collections with indexes
        collections = [
            ("users", [("email", 1)]),
            ("assessments", [("created_by", 1), ("status", 1)]),
            ("custom_controls", [("status", 1), ("frameworks", 1)]),
            ("control_tests", [("control_id", 1), ("status", 1)]),
            ("control_gaps", [("framework", 1), ("status", 1)]),
            ("gap_remediations", [("gap_id", 1), ("status", 1)]),
            ("ai_systems", [("risk_category", 1)]),
            ("automated_test_runs", [("control_id", 1)]),
            ("issues", [("status", 1), ("priority", 1)]),
            ("workflows", [("active", 1)]),
            ("agent_activities", [("session_id", 1)]),
            ("model_metrics", [("session_id", 1)]),
            ("knowledge_entities", [("entity_type", 1)]),
            ("knowledge_relations", [("source_entity_id", 1)]),
            ("trend_data", [("metric_type", 1), ("timestamp", -1)])
        ]
        
        for collection_name, indexes in collections:
            collection = db[collection_name]
            for index_fields in indexes:
                if isinstance(index_fields, tuple):
                    await collection.create_index([index_fields])
                else:
                    await collection.create_index(index_fields)
        
        logger.info(f"Initialized database for tenant: {tenant.id}")
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._tenants.get(tenant_id)
    
    async def list_tenants(self) -> List[Tenant]:
        """List all tenants."""
        return list(self._tenants.values())
    
    async def suspend_tenant(self, tenant_id: str) -> bool:
        """Suspend a tenant (blocks access but preserves data)."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        tenant.status = "suspended"
        
        # Update in master database
        master_client = await self.get_master_client()
        master_db = master_client[self.default_db_name]
        await master_db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"status": "suspended"}}
        )
        
        logger.info(f"Suspended tenant: {tenant_id}")
        return True
    
    async def activate_tenant(self, tenant_id: str) -> bool:
        """Reactivate a suspended tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        tenant.status = "active"
        
        master_client = await self.get_master_client()
        master_db = master_client[self.default_db_name]
        await master_db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"status": "active"}}
        )
        
        logger.info(f"Activated tenant: {tenant_id}")
        return True
    
    async def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id: Tenant to delete
            hard_delete: If True, actually drops the database
        """
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        
        if tenant_id == "default":
            raise ValueError("Cannot delete default tenant")
        
        if hard_delete:
            # Drop the tenant's database
            client = await self.get_master_client()
            await client.drop_database(tenant.database_name)
            logger.warning(f"Hard deleted tenant database: {tenant.database_name}")
        
        tenant.status = "deleted"
        
        # Update in master database
        master_client = await self.get_master_client()
        master_db = master_client[self.default_db_name]
        await master_db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"status": "deleted"}}
        )
        
        # Remove from active tenants
        del self._tenants[tenant_id]
        
        logger.info(f"Deleted tenant: {tenant_id}")
        return True
    
    async def load_tenants(self):
        """Load tenants from master database on startup."""
        master_client = await self.get_master_client()
        master_db = master_client[self.default_db_name]
        
        async for tenant_doc in master_db.tenants.find({"status": {"$ne": "deleted"}}):
            tenant = Tenant(
                id=tenant_doc["id"],
                name=tenant_doc["name"],
                display_name=tenant_doc.get("display_name", tenant_doc["name"]),
                database_name=tenant_doc["database_name"],
                created_at=datetime.fromisoformat(tenant_doc["created_at"]) if isinstance(tenant_doc["created_at"], str) else tenant_doc["created_at"],
                status=tenant_doc.get("status", "active"),
                settings=tenant_doc.get("settings", {})
            )
            self._tenants[tenant.id] = tenant
        
        logger.info(f"Loaded {len(self._tenants)} tenants")
    
    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get statistics for a tenant."""
        db = await self.get_tenant_db(tenant_id)
        
        stats = {
            "tenant_id": tenant_id,
            "collections": {}
        }
        
        collection_names = await db.list_collection_names()
        for name in collection_names:
            count = await db[name].count_documents({})
            stats["collections"][name] = count
        
        return stats


# Dependency injection helper
def get_tenant_service() -> MultiTenancyService:
    """Get the multi-tenancy service instance."""
    return MultiTenancyService()


# Context manager for tenant-scoped operations
class TenantContext:
    """Context manager for tenant-scoped database operations."""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.service = MultiTenancyService()
        self.db = None
    
    async def __aenter__(self):
        self.db = await self.service.get_tenant_db(self.tenant_id)
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # Connection pooling handles cleanup
