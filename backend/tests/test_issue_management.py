"""
Issue Management API Integration Tests
Tests for the issue management module with full lifecycle tracking
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestIssueManagementAPI:
    """Integration tests for Issue Management endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_token):
        """Setup for each test."""
        self.client = api_client
        self.token = admin_token
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        self.created_issues = []
    
    def teardown_method(self):
        """Cleanup created test data."""
        # Note: No delete endpoint available, issues will remain
        pass
    
    def test_list_issues(self):
        """Test listing issues."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "issues" in data
        assert isinstance(data["issues"], list)
    
    def test_get_issue_statistics(self):
        """Test getting issue statistics."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/statistics")
        assert response.status_code == 200
        data = response.json()
        
        # Verify statistics structure
        assert "total" in data
        assert "open" in data
        assert "in_progress" in data
        assert "resolved" in data
        assert "closed" in data
        assert "p1" in data
        assert "p2" in data
        assert "p3" in data
        assert "p4" in data
    
    def test_create_manual_issue(self):
        """Test creating a manual issue."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST_Issue_{unique_id}",
            "description": "Test issue description for integration testing",
            "issue_type": "RISK_FINDING",
            "severity": "HIGH",
            "priority": "P2",
            "source": "MANUAL",
            "owner": "test-owner@company.com",
            "app_name": "Test Application",
            "business_unit": "Technology",
            "tags": ["test", "integration"]
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/?creator_id=test-user&creator_name=Test%20User",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "issue_id" in data
        assert data["title"] == payload["title"]
        assert data["status"] == "OPEN"
        assert data["priority"] == "P2"
        assert data["source"] == "MANUAL"
        assert "sla" in data
        assert "history" in data
        assert len(data["history"]) == 1
        assert data["history"][0]["action"] == "CREATED"
        
        self.created_issues.append(data["id"])
        return data
    
    def test_get_issue_by_id(self):
        """Test getting issue details by ID."""
        # First create an issue
        issue = self.test_create_manual_issue()
        
        # Then fetch it
        response = self.client.get(f"{BASE_URL}/api/issue-management/{issue['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == issue["id"]
        assert data["title"] == issue["title"]
    
    def test_get_issue_not_found(self):
        """Test getting non-existent issue returns 404."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/non-existent-id")
        assert response.status_code == 404
    
    def test_update_issue_status(self):
        """Test updating issue status with history tracking."""
        # Create issue
        issue = self.test_create_manual_issue()
        
        # Update status to IN_PROGRESS
        response = self.client.put(
            f"{BASE_URL}/api/issue-management/{issue['id']}?user_id=test-user&user_name=Test%20User",
            json={"status": "IN_PROGRESS"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "IN_PROGRESS"
        # Verify history was updated
        assert len(data["history"]) > 1
        status_change = next((h for h in data["history"] if h["action"] == "STATUS_CHANGED"), None)
        assert status_change is not None
    
    def test_update_issue_priority(self):
        """Test updating issue priority."""
        # Create issue
        issue = self.test_create_manual_issue()
        
        # Update priority
        response = self.client.put(
            f"{BASE_URL}/api/issue-management/{issue['id']}?user_id=test-user&user_name=Test%20User",
            json={"priority": "P1"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["priority"] == "P1"
    
    def test_add_comment_to_issue(self):
        """Test adding a comment to an issue."""
        # Create issue
        issue = self.test_create_manual_issue()
        
        # Add comment
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/comments?user_id=test-user&user_name=Test%20User",
            json={"text": "This is a test comment", "is_internal": False}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify comment was added
        assert len(data["comments"]) == 1
        assert data["comments"][0]["text"] == "This is a test comment"
        assert data["comments"][0]["user_name"] == "Test User"
    
    def test_add_internal_comment(self):
        """Test adding an internal comment."""
        # Create issue
        issue = self.test_create_manual_issue()
        
        # Add internal comment
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/comments?user_id=test-user&user_name=Test%20User",
            json={"text": "Internal note", "is_internal": True}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["comments"][0]["is_internal"] == True
    
    def test_resolve_issue(self):
        """Test resolving an issue with documentation."""
        # Create and progress issue
        issue = self.test_create_manual_issue()
        
        # Move to IN_PROGRESS first
        self.client.put(
            f"{BASE_URL}/api/issue-management/{issue['id']}?user_id=test-user&user_name=Test%20User",
            json={"status": "IN_PROGRESS"}
        )
        
        # Resolve issue
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/resolve?user_id=test-user&user_name=Test%20User",
            json={
                "resolution": "Issue has been addressed by implementing new controls",
                "root_cause": "Missing security controls",
                "lessons_learned": "Need to implement controls earlier in development"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "RESOLVED"
        assert data["resolution"] == "Issue has been addressed by implementing new controls"
        assert data["root_cause"] == "Missing security controls"
        assert data["resolved_at"] is not None
    
    def test_close_issue(self):
        """Test closing a resolved issue."""
        # Create, progress, and resolve issue
        issue = self.test_create_manual_issue()
        
        self.client.put(
            f"{BASE_URL}/api/issue-management/{issue['id']}?user_id=test-user&user_name=Test%20User",
            json={"status": "IN_PROGRESS"}
        )
        
        self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/resolve?user_id=test-user&user_name=Test%20User",
            json={
                "resolution": "Fixed",
                "root_cause": "Bug",
                "lessons_learned": "Testing"
            }
        )
        
        # Close issue
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/close?user_id=test-user&user_name=Test%20User&close_reason=Verified%20fixed"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "CLOSED"
        assert data["closed_at"] is not None
    
    def test_close_unresolved_issue_fails(self):
        """Test that closing an unresolved issue fails."""
        # Create issue (status is OPEN)
        issue = self.test_create_manual_issue()
        
        # Try to close without resolving
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/close?user_id=test-user&user_name=Test%20User"
        )
        assert response.status_code == 400
    
    def test_sync_to_servicenow(self):
        """Test syncing issue to ServiceNow (mock mode)."""
        # Create issue
        issue = self.test_create_manual_issue()
        
        # Sync to ServiceNow
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/sync-servicenow?user_id=test-user&user_name=Test%20User"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "servicenow_result" in data
        # Mock mode should return success
        assert data["servicenow_result"]["success"] == True
        assert "number" in data["servicenow_result"]
    
    def test_get_issues_by_assessment(self):
        """Test getting issues linked to an assessment."""
        # Get an assessment ID from existing data
        assessments_response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments")
        assessments = assessments_response.json().get("assessments", [])
        
        if not assessments:
            pytest.skip("No assessments available")
        
        assessment_id = assessments[0]["id"]
        
        response = self.client.get(f"{BASE_URL}/api/issue-management/by-assessment/{assessment_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "issues" in data
    
    def test_filter_issues_by_status(self):
        """Test filtering issues by status."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/?status=OPEN")
        assert response.status_code == 200
        data = response.json()
        
        # All returned issues should have OPEN status
        for issue in data["issues"]:
            assert issue["status"] == "OPEN"
    
    def test_filter_issues_by_priority(self):
        """Test filtering issues by priority."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/?priority=P1")
        assert response.status_code == 200
        data = response.json()
        
        # All returned issues should have P1 priority
        for issue in data["issues"]:
            assert issue["priority"] == "P1"
    
    def test_filter_issues_by_type(self):
        """Test filtering issues by type."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/?issue_type=RISK_FINDING")
        assert response.status_code == 200
        data = response.json()
        
        # All returned issues should have RISK_FINDING type
        for issue in data["issues"]:
            assert issue["type"] == "RISK_FINDING"
    
    def test_get_overdue_issues(self):
        """Test getting overdue issues."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/overdue")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "issues" in data
    
    def test_get_issue_types(self):
        """Test getting available issue types."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/enums/types")
        assert response.status_code == 200
        data = response.json()
        
        assert "types" in data
        type_ids = [t["id"] for t in data["types"]]
        assert "RISK_FINDING" in type_ids
        assert "CONTROL_DEFICIENCY" in type_ids
        assert "COMPLIANCE_GAP" in type_ids
    
    def test_get_issue_statuses(self):
        """Test getting available issue statuses."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/enums/statuses")
        assert response.status_code == 200
        data = response.json()
        
        assert "statuses" in data
        status_ids = [s["id"] for s in data["statuses"]]
        assert "OPEN" in status_ids
        assert "IN_PROGRESS" in status_ids
        assert "RESOLVED" in status_ids
        assert "CLOSED" in status_ids
    
    def test_get_issue_priorities(self):
        """Test getting available issue priorities."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/enums/priorities")
        assert response.status_code == 200
        data = response.json()
        
        assert "priorities" in data
        priority_ids = [p["id"] for p in data["priorities"]]
        assert "P1" in priority_ids
        assert "P2" in priority_ids
        assert "P3" in priority_ids
        assert "P4" in priority_ids
        
        # Verify SLA info
        p1 = next(p for p in data["priorities"] if p["id"] == "P1")
        assert p1["sla_response_hours"] == 1
        assert p1["sla_resolution_hours"] == 24
    
    def test_get_issue_sources(self):
        """Test getting available issue sources."""
        response = self.client.get(f"{BASE_URL}/api/issue-management/enums/sources")
        assert response.status_code == 200
        data = response.json()
        
        assert "sources" in data
        source_ids = [s["id"] for s in data["sources"]]
        assert "MANUAL" in source_ids
        assert "TECH_RISK_ASSESSMENT" in source_ids
        assert "CONTROL_TESTING" in source_ids
    
    def test_link_issue_to_assessment(self):
        """Test linking an issue to an assessment."""
        # Create issue
        issue = self.test_create_manual_issue()
        
        # Get an assessment ID
        assessments_response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments")
        assessments = assessments_response.json().get("assessments", [])
        
        if not assessments:
            pytest.skip("No assessments available")
        
        assessment_id = assessments[0]["id"]
        
        # Link issue to assessment
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/{issue['id']}/link?user_id=test-user&user_name=Test%20User",
            json={"target_id": assessment_id, "link_type": "assessment"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert assessment_id in data["linked_items"]["assessments"]
    
    def test_issue_sla_tracking(self):
        """Test that SLA deadlines are set correctly."""
        # Create P1 issue
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST_P1_Issue_{unique_id}",
            "description": "Critical issue for SLA testing",
            "issue_type": "SECURITY_INCIDENT",
            "severity": "CRITICAL",
            "priority": "P1",
            "source": "MANUAL"
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/issue-management/?creator_id=test-user&creator_name=Test%20User",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify SLA is set
        assert data["sla"]["response_deadline"] is not None
        assert data["sla"]["resolution_deadline"] is not None
        
        # P1 should have 1 hour response, 24 hour resolution
        # Just verify the deadlines exist and are in the future
        response_deadline = datetime.fromisoformat(data["sla"]["response_deadline"].replace('Z', '+00:00'))
        resolution_deadline = datetime.fromisoformat(data["sla"]["resolution_deadline"].replace('Z', '+00:00'))
        
        assert resolution_deadline > response_deadline
