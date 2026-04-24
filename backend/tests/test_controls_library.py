"""
Backend tests for Custom Controls Library and Control Testing features
Tests LOD1/LOD2 approval workflow and control testing lifecycle
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCustomControlsLibrary:
    """Test Custom Controls Library CRUD and approval workflow"""

    def test_lod1_create_control_draft_status(self, lod1_client, unique_id):
        """LOD1 creates control - should be DRAFT status"""
        control_data = {
            "name": f"TEST_Control_{unique_id}",
            "description": "Test control for MFA enforcement",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF", "ISO 27001"],
            "regulatory_references": ["PR.AC-1"],
            "implementation_guidance": "Implement MFA for all users",
            "testing_procedure": "Verify MFA is enabled",
            "evidence_requirements": ["MFA config screenshot"],
            "frequency": "Annual",
            "is_ai_control": False
        }
        
        response = lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        assert response.status_code == 200, f"Failed to create control: {response.text}"
        
        data = response.json()
        assert data['name'] == control_data['name']
        assert data['status'] == 'DRAFT', "LOD1 created control should be DRAFT"
        assert data['approved_by'] is None
        assert data['approved_at'] is None
        
        return data['id']

    def test_lod2_create_control_approved_status(self, lod2_client, unique_id):
        """LOD2 creates control - should be auto-APPROVED"""
        control_data = {
            "name": f"TEST_Control_LOD2_{unique_id}",
            "description": "Test control created by LOD2",
            "category": "ADMINISTRATIVE",
            "frameworks": ["SOC2"],
            "frequency": "Quarterly"
        }
        
        response = lod2_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        assert response.status_code == 200, f"Failed to create control: {response.text}"
        
        data = response.json()
        assert data['status'] == 'APPROVED', "LOD2 created control should be auto-APPROVED"
        assert data['approved_by'] is not None
        
        return data['id']

    def test_admin_create_control_approved_status(self, admin_client, unique_id):
        """Admin creates control - should be auto-APPROVED"""
        control_data = {
            "name": f"TEST_Control_Admin_{unique_id}",
            "description": "Test control created by Admin",
            "category": "OPERATIONAL",
            "frameworks": ["PCI-DSS"],
            "frequency": "Monthly"
        }
        
        response = admin_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        assert response.status_code == 200, f"Failed to create control: {response.text}"
        
        data = response.json()
        assert data['status'] == 'APPROVED', "Admin created control should be auto-APPROVED"
        
        return data['id']

    def test_list_controls_library(self, lod1_client):
        """List all controls from library"""
        response = lod1_client.get(f"{BASE_URL}/api/controls/library")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_filter_controls_by_framework(self, lod1_client, unique_id):
        """Filter controls by framework"""
        # First create a control with specific framework
        control_data = {
            "name": f"TEST_NIST_Control_{unique_id}",
            "description": "NIST specific control",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        
        # Filter by framework
        response = lod1_client.get(f"{BASE_URL}/api/controls/library?framework=NIST CSF")
        assert response.status_code == 200
        
        data = response.json()
        for control in data:
            assert "NIST CSF" in control.get('frameworks', [])

    def test_filter_ai_controls(self, lod1_client, unique_id):
        """Filter AI-specific controls"""
        # Create an AI control
        control_data = {
            "name": f"TEST_AI_Control_{unique_id}",
            "description": "AI governance control",
            "category": "AI_GOVERNANCE",
            "frameworks": ["EU_AI_ACT"],
            "frequency": "Quarterly",
            "is_ai_control": True,
            "ai_risk_category": "HIGH"
        }
        lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        
        # Filter AI controls
        response = lod1_client.get(f"{BASE_URL}/api/controls/library?is_ai_control=true")
        assert response.status_code == 200
        
        data = response.json()
        for control in data:
            assert control.get('is_ai_control') == True

    def test_filter_pending_review_controls(self, lod2_client):
        """Filter controls pending review (LOD2 only)"""
        response = lod2_client.get(f"{BASE_URL}/api/controls/library?status=PENDING_REVIEW")
        assert response.status_code == 200
        
        data = response.json()
        for control in data:
            assert control.get('status') == 'PENDING_REVIEW'

    def test_get_control_by_id(self, lod1_client, unique_id):
        """Get specific control by ID"""
        # Create control first
        control_data = {
            "name": f"TEST_GetById_{unique_id}",
            "description": "Test control for get by ID",
            "category": "TECHNICAL",
            "frameworks": ["ISO 27001"],
            "frequency": "Annual"
        }
        create_response = lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        # Get by ID
        response = lod1_client.get(f"{BASE_URL}/api/controls/library/{control_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == control_id
        assert data['name'] == control_data['name']

    def test_get_nonexistent_control_returns_404(self, lod1_client):
        """Get non-existent control returns 404"""
        response = lod1_client.get(f"{BASE_URL}/api/controls/library/nonexistent-id")
        assert response.status_code == 404

    def test_update_control(self, lod1_client, unique_id):
        """Update a control"""
        # Create control first
        control_data = {
            "name": f"TEST_Update_{unique_id}",
            "description": "Original description",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        # Update control
        update_data = {
            "description": "Updated description",
            "frequency": "Quarterly"
        }
        response = lod1_client.put(f"{BASE_URL}/api/controls/library/{control_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['description'] == "Updated description"
        assert data['frequency'] == "Quarterly"


class TestControlApprovalWorkflow:
    """Test LOD2 approval workflow for controls"""

    def test_lod2_approve_lod1_control(self, lod1_client, lod2_client, unique_id):
        """LOD2 approves LOD1 created control"""
        # LOD1 creates control
        control_data = {
            "name": f"TEST_Approve_{unique_id}",
            "description": "Control to be approved",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        assert create_response.json()['status'] == 'DRAFT'
        
        # LOD2 approves
        response = lod2_client.post(f"{BASE_URL}/api/controls/library/{control_id}/approve")
        assert response.status_code == 200
        
        # Verify status changed
        get_response = lod1_client.get(f"{BASE_URL}/api/controls/library/{control_id}")
        assert get_response.json()['status'] == 'APPROVED'
        assert get_response.json()['approved_by'] is not None

    def test_lod2_reject_control(self, lod1_client, lod2_client, unique_id):
        """LOD2 rejects a control"""
        # LOD1 creates control
        control_data = {
            "name": f"TEST_Reject_{unique_id}",
            "description": "Control to be rejected",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        # LOD2 rejects
        response = lod2_client.post(
            f"{BASE_URL}/api/controls/library/{control_id}/reject",
            params={"reason": "Insufficient detail"}
        )
        assert response.status_code == 200
        
        # Verify status changed
        get_response = lod1_client.get(f"{BASE_URL}/api/controls/library/{control_id}")
        assert get_response.json()['status'] == 'REJECTED'

    def test_lod1_cannot_approve_control(self, lod1_client, unique_id):
        """LOD1 cannot approve controls - should get 403"""
        # Create control
        control_data = {
            "name": f"TEST_LOD1Approve_{unique_id}",
            "description": "Control LOD1 tries to approve",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod1_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        # LOD1 tries to approve - should fail
        response = lod1_client.post(f"{BASE_URL}/api/controls/library/{control_id}/approve")
        assert response.status_code == 403


class TestControlTesting:
    """Test Control Testing lifecycle"""

    def test_create_control_test(self, lod1_client, lod2_client, unique_id):
        """Create a control test (LOD1 tests)"""
        # First create and approve a control
        control_data = {
            "name": f"TEST_ForTesting_{unique_id}",
            "description": "Control to be tested",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod2_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        # Create test
        test_data = {
            "control_id": control_id,
            "test_type": "Manual",
            "test_procedure": "Verify MFA is enabled for all users",
            "expected_result": "All users have MFA enabled"
        }
        response = lod1_client.post(f"{BASE_URL}/api/control-tests", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['control_id'] == control_id
        assert data['status'] == 'IN_PROGRESS'
        assert data['tester_role'] == 'LOD1_USER'
        
        return data['id']

    def test_list_control_tests(self, lod1_client):
        """List control tests"""
        response = lod1_client.get(f"{BASE_URL}/api/control-tests")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_update_control_test_results(self, lod1_client, lod2_client, unique_id):
        """Update control test with results"""
        # Create control and test
        control_data = {
            "name": f"TEST_UpdateTest_{unique_id}",
            "description": "Control for test update",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod2_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        test_data = {
            "control_id": control_id,
            "test_type": "Manual",
            "test_procedure": "Verify encryption",
            "expected_result": "Data encrypted at rest"
        }
        test_response = lod1_client.post(f"{BASE_URL}/api/control-tests", json=test_data)
        test_id = test_response.json()['id']
        
        # Update test results
        update_data = {
            "actual_result": "All data is encrypted with AES-256",
            "evidence_collected": ["encryption_config.json", "audit_log.txt"],
            "effectiveness_rating": "EFFECTIVE",
            "findings": "Control is operating effectively"
        }
        response = lod1_client.put(f"{BASE_URL}/api/control-tests/{test_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['actual_result'] == update_data['actual_result']
        assert data['effectiveness_rating'] == 'EFFECTIVE'

    def test_submit_control_test_for_review(self, lod1_client, lod2_client, unique_id):
        """Submit control test for LOD2 review"""
        # Create control and test
        control_data = {
            "name": f"TEST_Submit_{unique_id}",
            "description": "Control for submit test",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod2_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        test_data = {
            "control_id": control_id,
            "test_type": "Manual",
            "test_procedure": "Verify access controls",
            "expected_result": "Access properly restricted"
        }
        test_response = lod1_client.post(f"{BASE_URL}/api/control-tests", json=test_data)
        test_id = test_response.json()['id']
        
        # Submit for review
        response = lod1_client.post(f"{BASE_URL}/api/control-tests/{test_id}/submit")
        assert response.status_code == 200
        
        # Verify status changed
        get_response = lod1_client.get(f"{BASE_URL}/api/control-tests")
        tests = [t for t in get_response.json() if t['id'] == test_id]
        if tests:
            assert tests[0]['status'] == 'PENDING_REVIEW'

    def test_lod2_review_control_test_approve(self, lod1_client, lod2_client, unique_id):
        """LOD2 reviews and approves control test"""
        # Create control and test
        control_data = {
            "name": f"TEST_Review_{unique_id}",
            "description": "Control for review test",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod2_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        test_data = {
            "control_id": control_id,
            "test_type": "Manual",
            "test_procedure": "Verify logging",
            "expected_result": "All events logged"
        }
        test_response = lod1_client.post(f"{BASE_URL}/api/control-tests", json=test_data)
        test_id = test_response.json()['id']
        
        # Submit for review
        lod1_client.post(f"{BASE_URL}/api/control-tests/{test_id}/submit")
        
        # LOD2 reviews
        review_data = {
            "review_comments": "Test results verified and approved",
            "review_status": "APPROVED"
        }
        response = lod2_client.post(f"{BASE_URL}/api/control-tests/{test_id}/review", json=review_data)
        assert response.status_code == 200

    def test_lod1_cannot_review_test(self, lod1_client, lod2_client, unique_id):
        """LOD1 cannot review control tests - should get 403"""
        # Create control and test
        control_data = {
            "name": f"TEST_LOD1Review_{unique_id}",
            "description": "Control for LOD1 review attempt",
            "category": "TECHNICAL",
            "frameworks": ["NIST CSF"],
            "frequency": "Annual"
        }
        create_response = lod2_client.post(f"{BASE_URL}/api/controls/library", json=control_data)
        control_id = create_response.json()['id']
        
        test_data = {
            "control_id": control_id,
            "test_type": "Manual",
            "test_procedure": "Verify controls",
            "expected_result": "Controls effective"
        }
        test_response = lod1_client.post(f"{BASE_URL}/api/control-tests", json=test_data)
        test_id = test_response.json()['id']
        
        # LOD1 tries to review - should fail
        review_data = {
            "review_comments": "Trying to review",
            "review_status": "APPROVED"
        }
        response = lod1_client.post(f"{BASE_URL}/api/control-tests/{test_id}/review", json=review_data)
        assert response.status_code == 403

    def test_filter_pending_review_tests(self, lod2_client):
        """Filter tests pending review"""
        response = lod2_client.get(f"{BASE_URL}/api/control-tests?pending_review=true")
        assert response.status_code == 200
        
        data = response.json()
        for test in data:
            assert test.get('status') == 'PENDING_REVIEW'
