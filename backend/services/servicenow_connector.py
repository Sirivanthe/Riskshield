# ServiceNow Connector
# Integration with ServiceNow for GRC ticket management

import os
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class TicketPriority(str, Enum):
    CRITICAL = "1"
    HIGH = "2"
    MEDIUM = "3"
    LOW = "4"

class TicketState(str, Enum):
    NEW = "1"
    IN_PROGRESS = "2"
    ON_HOLD = "3"
    RESOLVED = "4"
    CLOSED = "5"
    CANCELED = "6"

@dataclass
class ServiceNowTicket:
    """Represents a ServiceNow incident/task ticket."""
    short_description: str
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category: str = "Risk Management"
    subcategory: str = "Control Deficiency"
    assignment_group: str = "IT Risk Management"
    assigned_to: str = ""
    caller_id: str = ""
    impact: str = "3"
    urgency: str = "3"
    cmdb_ci: str = ""  # Configuration item
    u_risk_id: str = ""  # Custom field for risk ID
    u_control_id: str = ""  # Custom field for control ID
    u_framework: str = ""  # Custom field for framework

@dataclass
class ServiceNowConfig:
    """ServiceNow connection configuration."""
    instance_url: str
    username: str = ""
    password: str = ""
    api_token: str = ""
    auth_type: str = "basic"  # "basic" | "token"
    api_version: str = "v2"
    timeout: int = 30

class ServiceNowConnector:
    """
    ServiceNow REST API connector for GRC integration.
    
    Features:
    - Create incidents/tasks for risk findings
    - Update ticket status
    - Query existing tickets
    - Sync control test results
    """
    
    def __init__(self, config: ServiceNowConfig = None):
        self.config = config or self._load_config_from_env()
        self._client = None
        self._mock_mode = not self.config or not self.config.instance_url or not (
            (self.config.auth_type == "basic" and self.config.username and self.config.password)
            or (self.config.auth_type == "token" and self.config.api_token)
        )
        
        if self._mock_mode:
            logger.info("ServiceNow connector running in MOCK mode")
            self._mock_tickets: Dict[str, Dict] = {}
            self._mock_counter = 1000

    def update_config(self, config: Optional[ServiceNowConfig]) -> None:
        """Swap the active configuration (used when user saves creds via UI)."""
        self.config = config
        # Invalidate any cached HTTP client so the next call uses fresh creds.
        self._client = None
        self._mock_mode = not self.config or not self.config.instance_url or not (
            (self.config.auth_type == "basic" and self.config.username and self.config.password)
            or (self.config.auth_type == "token" and self.config.api_token)
        )
        if self._mock_mode:
            logger.info("ServiceNow connector switched to MOCK mode")
            if not hasattr(self, "_mock_tickets"):
                self._mock_tickets = {}
                self._mock_counter = 1000
        else:
            logger.info(
                f"ServiceNow connector connected to {self.config.instance_url} "
                f"via {self.config.auth_type} auth"
            )
    
    def _load_config_from_env(self) -> Optional[ServiceNowConfig]:
        """Load configuration from environment variables (fallback only)."""
        instance_url = os.environ.get('SERVICENOW_INSTANCE_URL')
        username = os.environ.get('SERVICENOW_USERNAME')
        password = os.environ.get('SERVICENOW_PASSWORD')
        api_token = os.environ.get('SERVICENOW_API_TOKEN')

        if not instance_url:
            return None
        if api_token:
            return ServiceNowConfig(
                instance_url=instance_url,
                api_token=api_token,
                auth_type="token",
            )
        if username and password:
            return ServiceNowConfig(
                instance_url=instance_url,
                username=username,
                password=password,
                auth_type="basic",
            )
        return None
    
    @property
    def is_configured(self) -> bool:
        """Check if ServiceNow is properly configured."""
        return not self._mock_mode
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not self._client:
            kwargs = dict(
                base_url=f"{self.config.instance_url}/api/now/{self.config.api_version}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=self.config.timeout,
            )
            if self.config.auth_type == "token" and self.config.api_token:
                kwargs["headers"]["Authorization"] = f"Bearer {self.config.api_token}"
            elif self.config.username and self.config.password:
                kwargs["auth"] = (self.config.username, self.config.password)
            self._client = httpx.AsyncClient(**kwargs)
        return self._client

    async def test_connection(self) -> Dict[str, Any]:
        """Ping a lightweight endpoint to verify credentials."""
        if self._mock_mode:
            return {"success": False, "mode": "mock", "message": "No credentials configured"}
        try:
            client = await self._get_client()
            resp = await client.get("/table/sys_user?sysparm_limit=1")
            resp.raise_for_status()
            return {"success": True, "mode": "live", "status_code": resp.status_code}
        except httpx.HTTPStatusError as e:
            return {"success": False, "mode": "live", "status_code": e.response.status_code, "error": str(e)}
        except Exception as e:
            return {"success": False, "mode": "live", "error": str(e)}

    async def close(self) -> None:
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None
    
    async def create_incident(self, ticket: ServiceNowTicket) -> Dict[str, Any]:
        """
        Create a new incident in ServiceNow.
        
        Returns:
            Created ticket details including sys_id and number
        """
        if self._mock_mode:
            return self._mock_create_ticket(ticket, "incident")
        
        client = await self._get_client()
        
        payload = {
            "short_description": ticket.short_description,
            "description": ticket.description,
            "priority": ticket.priority.value,
            "category": ticket.category,
            "subcategory": ticket.subcategory,
            "assignment_group": ticket.assignment_group,
            "impact": ticket.impact,
            "urgency": ticket.urgency
        }
        
        if ticket.assigned_to:
            payload["assigned_to"] = ticket.assigned_to
        if ticket.caller_id:
            payload["caller_id"] = ticket.caller_id
        if ticket.cmdb_ci:
            payload["cmdb_ci"] = ticket.cmdb_ci
        if ticket.u_risk_id:
            payload["u_risk_id"] = ticket.u_risk_id
        if ticket.u_control_id:
            payload["u_control_id"] = ticket.u_control_id
        if ticket.u_framework:
            payload["u_framework"] = ticket.u_framework
        
        try:
            response = await client.post("/table/incident", json=payload)
            response.raise_for_status()
            result = response.json()["result"]
            
            logger.info(f"Created ServiceNow incident: {result.get('number')}")
            return {
                "success": True,
                "sys_id": result.get("sys_id"),
                "number": result.get("number"),
                "state": result.get("state"),
                "created_on": result.get("sys_created_on")
            }
        except Exception as e:
            logger.error(f"Failed to create ServiceNow incident: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_risk_task(self, ticket: ServiceNowTicket) -> Dict[str, Any]:
        """Create a GRC risk task in ServiceNow."""
        if self._mock_mode:
            return self._mock_create_ticket(ticket, "sn_risk_task")
        
        client = await self._get_client()
        
        payload = {
            "short_description": ticket.short_description,
            "description": ticket.description,
            "priority": ticket.priority.value,
            "assignment_group": ticket.assignment_group
        }
        
        if ticket.u_risk_id:
            payload["risk"] = ticket.u_risk_id
        
        try:
            response = await client.post("/table/sn_risk_task", json=payload)
            response.raise_for_status()
            result = response.json()["result"]
            
            return {
                "success": True,
                "sys_id": result.get("sys_id"),
                "number": result.get("number"),
                "task_type": "risk_task"
            }
        except Exception as e:
            logger.error(f"Failed to create risk task: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_ticket(
        self, 
        table: str, 
        sys_id: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing ticket."""
        if self._mock_mode:
            return self._mock_update_ticket(sys_id, updates)
        
        client = await self._get_client()
        
        try:
            response = await client.patch(f"/table/{table}/{sys_id}", json=updates)
            response.raise_for_status()
            result = response.json()["result"]
            
            return {
                "success": True,
                "sys_id": result.get("sys_id"),
                "number": result.get("number"),
                "state": result.get("state")
            }
        except Exception as e:
            logger.error(f"Failed to update ticket: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_ticket(self, table: str, sys_id: str) -> Dict[str, Any]:
        """Get ticket details."""
        if self._mock_mode:
            return self._mock_tickets.get(sys_id, {"error": "Ticket not found"})
        
        client = await self._get_client()
        
        try:
            response = await client.get(f"/table/{table}/{sys_id}")
            response.raise_for_status()
            return response.json()["result"]
        except Exception as e:
            return {"error": str(e)}
    
    async def query_tickets(
        self, 
        table: str = "incident",
        query: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query tickets with optional filter."""
        if self._mock_mode:
            return list(self._mock_tickets.values())[:limit]
        
        client = await self._get_client()
        
        params = {"sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        
        try:
            response = await client.get(f"/table/{table}", params=params)
            response.raise_for_status()
            return response.json()["result"]
        except Exception as e:
            logger.error(f"Failed to query tickets: {e}")
            return []
    
    async def close_ticket(
        self, 
        table: str, 
        sys_id: str, 
        resolution_notes: str
    ) -> Dict[str, Any]:
        """Close a ticket with resolution notes."""
        return await self.update_ticket(table, sys_id, {
            "state": TicketState.RESOLVED.value,
            "close_notes": resolution_notes,
            "resolved_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Mock methods for development/testing
    def _mock_create_ticket(self, ticket: ServiceNowTicket, ticket_type: str) -> Dict[str, Any]:
        """Create a mock ticket for testing."""
        self._mock_counter += 1
        sys_id = f"mock-{self._mock_counter}"
        number = f"INC{self._mock_counter:07d}" if ticket_type == "incident" else f"RTSK{self._mock_counter:07d}"
        
        mock_ticket = {
            "sys_id": sys_id,
            "number": number,
            "short_description": ticket.short_description,
            "description": ticket.description,
            "priority": ticket.priority.value,
            "state": TicketState.NEW.value,
            "category": ticket.category,
            "assignment_group": ticket.assignment_group,
            "created_on": datetime.now(timezone.utc).isoformat(),
            "ticket_type": ticket_type
        }
        
        self._mock_tickets[sys_id] = mock_ticket
        
        logger.info(f"Created mock ServiceNow ticket: {number}")
        return {
            "success": True,
            "sys_id": sys_id,
            "number": number,
            "state": TicketState.NEW.value,
            "mock": True
        }
    
    def _mock_update_ticket(self, sys_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a mock ticket."""
        if sys_id not in self._mock_tickets:
            return {"success": False, "error": "Ticket not found"}
        
        self._mock_tickets[sys_id].update(updates)
        self._mock_tickets[sys_id]["updated_on"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": True,
            "sys_id": sys_id,
            "number": self._mock_tickets[sys_id].get("number"),
            "state": self._mock_tickets[sys_id].get("state"),
            "mock": True
        }
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Helper functions for common GRC operations
async def create_risk_incident(
    connector: ServiceNowConnector,
    risk_title: str,
    risk_description: str,
    risk_id: str,
    framework: str,
    severity: str = "MEDIUM",
    assignment_group: str = "IT Risk Management"
) -> Dict[str, Any]:
    """Create an incident for a risk finding."""
    priority_map = {
        "CRITICAL": TicketPriority.CRITICAL,
        "HIGH": TicketPriority.HIGH,
        "MEDIUM": TicketPriority.MEDIUM,
        "LOW": TicketPriority.LOW
    }
    
    ticket = ServiceNowTicket(
        short_description=f"[{framework}] {risk_title}",
        description=f"""Risk Finding from RiskShield Platform

Risk ID: {risk_id}
Framework: {framework}
Severity: {severity}

Description:
{risk_description}

This incident was automatically created by the RiskShield GRC integration.
""",
        priority=priority_map.get(severity, TicketPriority.MEDIUM),
        category="Risk Management",
        subcategory="Risk Finding",
        assignment_group=assignment_group,
        u_risk_id=risk_id,
        u_framework=framework
    )
    
    return await connector.create_incident(ticket)


async def create_control_deficiency_incident(
    connector: ServiceNowConnector,
    control_name: str,
    control_id: str,
    deficiency: str,
    framework: str,
    effectiveness: str = "INEFFECTIVE",
    assignment_group: str = "IT Risk Management"
) -> Dict[str, Any]:
    """Create an incident for a control deficiency."""
    priority_map = {
        "INEFFECTIVE": TicketPriority.HIGH,
        "PARTIALLY_EFFECTIVE": TicketPriority.MEDIUM,
        "NOT_TESTED": TicketPriority.LOW
    }
    
    ticket = ServiceNowTicket(
        short_description=f"[Control Deficiency] {control_name}",
        description=f"""Control Deficiency from RiskShield Platform

Control ID: {control_id}
Control Name: {control_name}
Framework: {framework}
Effectiveness: {effectiveness}

Deficiency Details:
{deficiency}

This incident was automatically created by the RiskShield GRC integration.
""",
        priority=priority_map.get(effectiveness, TicketPriority.MEDIUM),
        category="Risk Management",
        subcategory="Control Deficiency",
        assignment_group=assignment_group,
        u_control_id=control_id,
        u_framework=framework
    )
    
    return await connector.create_incident(ticket)
