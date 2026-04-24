# Enhanced Issue Management Service
# Full issue lifecycle with linking to assessments, control tests, and ServiceNow

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from db import db

logger = logging.getLogger(__name__)

class IssueStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REVIEW = "PENDING_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    DEFERRED = "DEFERRED"

class IssuePriority(str, Enum):
    P1 = "P1"  # Critical - immediate action
    P2 = "P2"  # High - action within 24 hours
    P3 = "P3"  # Medium - action within 1 week
    P4 = "P4"  # Low - action within 1 month

class IssueType(str, Enum):
    RISK_FINDING = "RISK_FINDING"
    CONTROL_DEFICIENCY = "CONTROL_DEFICIENCY"
    COMPLIANCE_GAP = "COMPLIANCE_GAP"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    AUDIT_FINDING = "AUDIT_FINDING"
    VULNERABILITY = "VULNERABILITY"
    POLICY_VIOLATION = "POLICY_VIOLATION"

class IssueSource(str, Enum):
    TECH_RISK_ASSESSMENT = "TECH_RISK_ASSESSMENT"
    CONTROL_TESTING = "CONTROL_TESTING"
    AUTOMATED_TESTING = "AUTOMATED_TESTING"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    AUDIT = "AUDIT"
    INCIDENT = "INCIDENT"
    MANUAL = "MANUAL"
    SERVICENOW = "SERVICENOW"

class IssueManagementService:
    """
    Comprehensive issue management service with:
    - Full issue lifecycle management
    - Linking to risk assessments and control tests
    - Case history tracking
    - ServiceNow integration
    - SLA tracking and escalation
    """
    
    # SLA definitions in hours
    SLA_DEFINITIONS = {
        "P1": {"response": 1, "resolution": 24},
        "P2": {"response": 4, "resolution": 72},
        "P3": {"response": 24, "resolution": 168},  # 1 week
        "P4": {"response": 48, "resolution": 720}   # 1 month
    }
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
    
    async def create_issue(
        self,
        title: str,
        description: str,
        issue_type: str,
        severity: str,
        priority: str,
        source: str,
        creator_id: str,
        creator_name: str,
        owner: str = None,
        source_id: str = None,
        source_risk_id: str = None,
        source_control_id: str = None,
        app_name: str = None,
        business_unit: str = None,
        due_date: str = None,
        tags: List[str] = None,
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new issue."""
        issue_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        # Calculate SLA deadlines
        sla = self.SLA_DEFINITIONS.get(priority, self.SLA_DEFINITIONS["P3"])
        response_deadline = (now + timedelta(hours=sla["response"])).isoformat()
        resolution_deadline = (now + timedelta(hours=sla["resolution"])).isoformat()
        
        # Calculate due date if not provided
        if not due_date:
            due_date = resolution_deadline[:10]
        
        issue = {
            "id": issue_id,
            "issue_id": f"ISS-{now.strftime('%Y%m%d')}-{issue_id[:6].upper()}",
            "title": title,
            "description": description,
            "type": issue_type,
            "severity": severity,
            "priority": priority,
            "status": IssueStatus.OPEN.value,
            "source": source,
            "source_id": source_id,
            "source_risk_id": source_risk_id,
            "source_control_id": source_control_id,
            "app_name": app_name,
            "business_unit": business_unit,
            "owner": owner,
            "owner_id": None,
            "creator_id": creator_id,
            "creator_name": creator_name,
            "assignee": None,
            "assignee_id": None,
            "due_date": due_date,
            "tags": tags or [],
            "attachments": attachments or [],
            "sla": {
                "response_deadline": response_deadline,
                "resolution_deadline": resolution_deadline,
                "response_met": None,
                "resolution_met": None,
                "first_response_at": None
            },
            "servicenow": {
                "synced": False,
                "incident_number": None,
                "sys_id": None,
                "last_sync": None
            },
            "linked_items": {
                "assessments": [],
                "control_tests": [],
                "remediations": [],
                "other_issues": []
            },
            "history": [{
                "action": "CREATED",
                "timestamp": now.isoformat(),
                "user_id": creator_id,
                "user_name": creator_name,
                "details": f"Issue created from {source}",
                "old_value": None,
                "new_value": None
            }],
            "comments": [],
            "resolution": None,
            "root_cause": None,
            "lessons_learned": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "resolved_at": None,
            "closed_at": None,
            "tenant_id": self.tenant_id
        }
        
        await db.issues.insert_one(issue)
        logger.info(f"Created issue: {issue['issue_id']}")
        
        return {k: v for k, v in issue.items() if k != "_id"}
    
    async def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get issue by ID."""
        issue = await db.issues.find_one(
            {"$or": [{"id": issue_id}, {"issue_id": issue_id}]},
            {"_id": 0}
        )
        return issue
    
    async def list_issues(
        self,
        status: str = None,
        priority: str = None,
        issue_type: str = None,
        source: str = None,
        owner: str = None,
        app_name: str = None,
        source_id: str = None,
        overdue_only: bool = False,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List issues with filters."""
        query = {"tenant_id": self.tenant_id}
        
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if issue_type:
            query["type"] = issue_type
        if source:
            query["source"] = source
        if owner:
            query["owner"] = {"$regex": owner, "$options": "i"}
        if app_name:
            query["app_name"] = {"$regex": app_name, "$options": "i"}
        if source_id:
            query["source_id"] = source_id
        if overdue_only:
            query["due_date"] = {"$lt": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
            query["status"] = {"$nin": [IssueStatus.RESOLVED.value, IssueStatus.CLOSED.value]}
        
        issues = await db.issues.find(query, {"_id": 0}).sort(
            [("priority", 1), ("created_at", -1)]
        ).limit(limit).to_list(limit)
        
        return issues
    
    async def update_issue(
        self,
        issue_id: str,
        updates: Dict[str, Any],
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Update an issue with history tracking."""
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError("Issue not found")
        
        now = datetime.now(timezone.utc)
        history_entries = []
        
        # Track changes
        tracked_fields = ["status", "priority", "severity", "owner", "assignee", "due_date"]
        for field in tracked_fields:
            if field in updates and updates[field] != issue.get(field):
                history_entries.append({
                    "action": f"{field.upper()}_CHANGED",
                    "timestamp": now.isoformat(),
                    "user_id": user_id,
                    "user_name": user_name,
                    "details": f"{field} changed",
                    "old_value": issue.get(field),
                    "new_value": updates[field]
                })
        
        # Handle status transitions
        if "status" in updates:
            new_status = updates["status"]
            if new_status == IssueStatus.IN_PROGRESS.value and not issue["sla"]["first_response_at"]:
                updates["sla.first_response_at"] = now.isoformat()
                updates["sla.response_met"] = now < datetime.fromisoformat(issue["sla"]["response_deadline"].replace('Z', '+00:00'))
            
            if new_status == IssueStatus.RESOLVED.value:
                updates["resolved_at"] = now.isoformat()
                updates["sla.resolution_met"] = now < datetime.fromisoformat(issue["sla"]["resolution_deadline"].replace('Z', '+00:00'))
            
            if new_status == IssueStatus.CLOSED.value:
                updates["closed_at"] = now.isoformat()
        
        updates["updated_at"] = now.isoformat()
        
        # Update with history
        await db.issues.update_one(
            {"id": issue["id"]},
            {
                "$set": updates,
                "$push": {"history": {"$each": history_entries}}
            }
        )
        
        return await self.get_issue(issue_id)
    
    async def add_comment(
        self,
        issue_id: str,
        comment_text: str,
        user_id: str,
        user_name: str,
        is_internal: bool = False
    ) -> Dict[str, Any]:
        """Add a comment to an issue."""
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError("Issue not found")
        
        now = datetime.now(timezone.utc)
        
        comment = {
            "id": str(uuid.uuid4()),
            "text": comment_text,
            "user_id": user_id,
            "user_name": user_name,
            "is_internal": is_internal,
            "created_at": now.isoformat()
        }
        
        await db.issues.update_one(
            {"id": issue["id"]},
            {
                "$push": {"comments": comment},
                "$set": {"updated_at": now.isoformat()}
            }
        )
        
        # Add to history
        await db.issues.update_one(
            {"id": issue["id"]},
            {
                "$push": {
                    "history": {
                        "action": "COMMENT_ADDED",
                        "timestamp": now.isoformat(),
                        "user_id": user_id,
                        "user_name": user_name,
                        "details": f"Comment added: {comment_text[:50]}..."
                    }
                }
            }
        )
        
        return await self.get_issue(issue_id)
    
    async def resolve_issue(
        self,
        issue_id: str,
        resolution: str,
        root_cause: str,
        lessons_learned: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Resolve an issue with documentation."""
        updates = {
            "status": IssueStatus.RESOLVED.value,
            "resolution": resolution,
            "root_cause": root_cause,
            "lessons_learned": lessons_learned
        }
        
        return await self.update_issue(issue_id, updates, user_id, user_name)
    
    async def close_issue(
        self,
        issue_id: str,
        user_id: str,
        user_name: str,
        close_reason: str = None
    ) -> Dict[str, Any]:
        """Close a resolved issue."""
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError("Issue not found")
        
        if issue["status"] != IssueStatus.RESOLVED.value:
            raise ValueError("Issue must be resolved before closing")
        
        updates = {"status": IssueStatus.CLOSED.value}
        if close_reason:
            updates["close_reason"] = close_reason
        
        return await self.update_issue(issue_id, updates, user_id, user_name)
    
    async def link_to_assessment(
        self,
        issue_id: str,
        assessment_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Link an issue to a tech risk assessment."""
        now = datetime.now(timezone.utc)
        
        await db.issues.update_one(
            {"id": issue_id},
            {
                "$addToSet": {"linked_items.assessments": assessment_id},
                "$push": {
                    "history": {
                        "action": "LINKED_TO_ASSESSMENT",
                        "timestamp": now.isoformat(),
                        "user_id": user_id,
                        "user_name": user_name,
                        "details": f"Linked to assessment: {assessment_id}"
                    }
                },
                "$set": {"updated_at": now.isoformat()}
            }
        )
        
        return await self.get_issue(issue_id)
    
    async def link_to_control_test(
        self,
        issue_id: str,
        control_test_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Link an issue to a control test."""
        now = datetime.now(timezone.utc)
        
        await db.issues.update_one(
            {"id": issue_id},
            {
                "$addToSet": {"linked_items.control_tests": control_test_id},
                "$push": {
                    "history": {
                        "action": "LINKED_TO_CONTROL_TEST",
                        "timestamp": now.isoformat(),
                        "user_id": user_id,
                        "user_name": user_name,
                        "details": f"Linked to control test: {control_test_id}"
                    }
                },
                "$set": {"updated_at": now.isoformat()}
            }
        )
        
        return await self.get_issue(issue_id)
    
    async def sync_to_servicenow(
        self,
        issue_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        """Sync issue to ServiceNow."""
        from services.servicenow_connector import (
            ServiceNowConnector, ServiceNowTicket, TicketPriority
        )
        
        issue = await self.get_issue(issue_id)
        if not issue:
            raise ValueError("Issue not found")
        
        connector = ServiceNowConnector()
        
        # Map priority
        priority_map = {
            "P1": TicketPriority.CRITICAL,
            "P2": TicketPriority.HIGH,
            "P3": TicketPriority.MEDIUM,
            "P4": TicketPriority.LOW
        }
        
        ticket = ServiceNowTicket(
            short_description=f"[{issue['issue_id']}] {issue['title']}",
            description=f"""Issue from RiskShield Platform

Issue ID: {issue['issue_id']}
Type: {issue['type']}
Severity: {issue['severity']}
Application: {issue.get('app_name', 'N/A')}

Description:
{issue['description']}

Source: {issue['source']}
Created: {issue['created_at']}
""",
            priority=priority_map.get(issue['priority'], TicketPriority.MEDIUM),
            category="Risk Management",
            subcategory=issue['type'],
            u_risk_id=issue.get('source_risk_id', ''),
            u_control_id=issue.get('source_control_id', '')
        )
        
        result = await connector.create_incident(ticket)
        
        if result.get("success"):
            now = datetime.now(timezone.utc)
            await db.issues.update_one(
                {"id": issue_id},
                {
                    "$set": {
                        "servicenow.synced": True,
                        "servicenow.incident_number": result.get("number"),
                        "servicenow.sys_id": result.get("sys_id"),
                        "servicenow.last_sync": now.isoformat(),
                        "updated_at": now.isoformat()
                    },
                    "$push": {
                        "history": {
                            "action": "SYNCED_TO_SERVICENOW",
                            "timestamp": now.isoformat(),
                            "user_id": user_id,
                            "user_name": user_name,
                            "details": f"Synced to ServiceNow: {result.get('number')}"
                        }
                    }
                }
            )
        
        return {
            "issue_id": issue_id,
            "servicenow_result": result
        }
    
    async def get_issues_by_assessment(self, assessment_id: str) -> List[Dict[str, Any]]:
        """Get all issues linked to an assessment."""
        issues = await db.issues.find(
            {
                "$or": [
                    {"source_id": assessment_id},
                    {"linked_items.assessments": assessment_id}
                ],
                "tenant_id": self.tenant_id
            },
            {"_id": 0}
        ).to_list(1000)
        
        return issues
    
    async def get_issues_by_control_test(self, control_test_id: str) -> List[Dict[str, Any]]:
        """Get all issues linked to a control test."""
        issues = await db.issues.find(
            {
                "$or": [
                    {"source_id": control_test_id},
                    {"linked_items.control_tests": control_test_id}
                ],
                "tenant_id": self.tenant_id
            },
            {"_id": 0}
        ).to_list(1000)
        
        return issues
    
    async def get_issue_statistics(self) -> Dict[str, Any]:
        """Get issue statistics for dashboard."""
        pipeline = [
            {"$match": {"tenant_id": self.tenant_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "open": {"$sum": {"$cond": [{"$eq": ["$status", "OPEN"]}, 1, 0]}},
                "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "IN_PROGRESS"]}, 1, 0]}},
                "resolved": {"$sum": {"$cond": [{"$eq": ["$status", "RESOLVED"]}, 1, 0]}},
                "closed": {"$sum": {"$cond": [{"$eq": ["$status", "CLOSED"]}, 1, 0]}},
                "p1": {"$sum": {"$cond": [{"$eq": ["$priority", "P1"]}, 1, 0]}},
                "p2": {"$sum": {"$cond": [{"$eq": ["$priority", "P2"]}, 1, 0]}},
                "p3": {"$sum": {"$cond": [{"$eq": ["$priority", "P3"]}, 1, 0]}},
                "p4": {"$sum": {"$cond": [{"$eq": ["$priority", "P4"]}, 1, 0]}},
            }}
        ]
        
        result = await db.issues.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            del stats["_id"]
            return stats
        
        return {
            "total": 0, "open": 0, "in_progress": 0, "resolved": 0, "closed": 0,
            "p1": 0, "p2": 0, "p3": 0, "p4": 0
        }
    
    async def get_overdue_issues(self) -> List[Dict[str, Any]]:
        """Get all overdue issues."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        issues = await db.issues.find(
            {
                "due_date": {"$lt": today},
                "status": {"$nin": [IssueStatus.RESOLVED.value, IssueStatus.CLOSED.value]},
                "tenant_id": self.tenant_id
            },
            {"_id": 0}
        ).sort("due_date", 1).to_list(1000)
        
        return issues
    
    async def create_issue_from_control_test(
        self,
        control_test_id: str,
        finding: str,
        creator_id: str,
        creator_name: str
    ) -> Dict[str, Any]:
        """Create an issue from a failed control test."""
        # Get control test details
        control_test = await db.control_tests.find_one({"id": control_test_id}, {"_id": 0})
        if not control_test:
            raise ValueError("Control test not found")
        
        return await self.create_issue(
            title=f"Control Deficiency: {control_test.get('control_name', 'Unknown Control')}",
            description=finding,
            issue_type=IssueType.CONTROL_DEFICIENCY.value,
            severity=control_test.get('effectiveness', 'MEDIUM'),
            priority="P2" if control_test.get('effectiveness') == 'INEFFECTIVE' else "P3",
            source=IssueSource.CONTROL_TESTING.value,
            creator_id=creator_id,
            creator_name=creator_name,
            source_id=control_test_id,
            source_control_id=control_test.get('control_id'),
            app_name=control_test.get('app_name')
        )
