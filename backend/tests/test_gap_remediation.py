"""
Backend integration tests for Gap Remediation API endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestGapAnalysisAPI:
    """Tests for /api/gap-analysis endpoint"""
    
    def test_get_gaps_returns_list(self, admin_client):
        """Test GET /api/gap-analysis returns a list"""
        response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_gaps_structure(self, admin_client):
        """Test that gaps have expected structure"""
        response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            gap = data[0]
            # Check required fields
            assert 'id' in gap
            assert 'gap_id' in gap
            assert 'framework' in gap
            assert 'requirement_id' in gap
            assert 'gap_description' in gap
            assert 'severity' in gap
            assert 'status' in gap
    
    def test_get_gaps_severity_values(self, admin_client):
        """Test that gap severity values are valid"""
        response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        valid_severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        for gap in data:
            assert gap['severity'] in valid_severities, f"Invalid severity: {gap['severity']}"
    
    def test_get_gaps_status_values(self, admin_client):
        """Test that gap status values are valid"""
        response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        valid_statuses = ['OPEN', 'IN_PROGRESS', 'REMEDIATED', 'ACCEPTED']
        for gap in data:
            assert gap['status'] in valid_statuses, f"Invalid status: {gap['status']}"


class TestGapRemediationAPI:
    """Tests for /api/gap-remediation endpoints"""
    
    def test_get_remediations_returns_list(self, admin_client):
        """Test GET /api/gap-remediation returns a list"""
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_remediations_structure(self, admin_client):
        """Test that remediations have expected structure"""
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            rem = data[0]
            # Check required fields
            assert 'id' in rem
            assert 'remediation_id' in rem
            assert 'gap_id' in rem
            assert 'gap_description' in rem
            assert 'framework' in rem
            assert 'priority' in rem
            assert 'status' in rem
            assert 'progress_percentage' in rem
    
    def test_get_remediation_by_id_not_found(self, admin_client):
        """Test GET /api/gap-remediation/{id} returns 404 for non-existent remediation"""
        fake_id = str(uuid.uuid4())
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation/{fake_id}")
        
        assert response.status_code == 404
    
    def test_get_recommendations_for_gap(self, admin_client):
        """Test GET /api/gap-remediation/recommendations/{gap_id} returns recommendations"""
        # First get a gap
        gaps_response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        assert gaps_response.status_code == 200
        gaps = gaps_response.json()
        
        if len(gaps) == 0:
            pytest.skip("No gaps available for testing")
        
        gap = gaps[0]
        gap_id = gap['id']
        
        # Get recommendations
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation/recommendations/{gap_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert 'gap_id' in data
        assert 'framework' in data
        assert 'requirement_id' in data
        assert 'recommendations' in data
    
    def test_get_recommendations_structure(self, admin_client):
        """Test that recommendations have expected structure"""
        # Get a gap
        gaps_response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        gaps = gaps_response.json()
        
        if len(gaps) == 0:
            pytest.skip("No gaps available for testing")
        
        gap_id = gaps[0]['id']
        
        # Get recommendations
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation/recommendations/{gap_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        recommendations = data['recommendations']
        
        # Check recommended_controls structure
        if 'recommended_controls' in recommendations and len(recommendations['recommended_controls']) > 0:
            ctrl = recommendations['recommended_controls'][0]
            assert 'name' in ctrl
            assert 'description' in ctrl
            assert 'implementation_effort' in ctrl
            assert 'effectiveness_estimate' in ctrl
    
    def test_get_recommendations_for_nonexistent_gap(self, admin_client):
        """Test GET /api/gap-remediation/recommendations/{gap_id} returns 404 for non-existent gap"""
        fake_id = str(uuid.uuid4())
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation/recommendations/{fake_id}")
        
        assert response.status_code == 404
    
    def test_create_remediation_for_gap(self, admin_client):
        """Test POST /api/gap-remediation creates a remediation plan"""
        # Get an OPEN gap
        gaps_response = admin_client.get(f"{BASE_URL}/api/gap-analysis")
        gaps = gaps_response.json()
        
        open_gaps = [g for g in gaps if g['status'] == 'OPEN']
        if len(open_gaps) == 0:
            pytest.skip("No open gaps available for testing")
        
        gap = open_gaps[0]
        
        # Create remediation
        response = admin_client.post(
            f"{BASE_URL}/api/gap-remediation",
            json={
                "gap_id": gap['id'],
                "priority": "HIGH"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        assert 'id' in data
        assert 'remediation_id' in data
        assert data['gap_id'] == gap['id']
        assert data['status'] == 'DRAFT'
    
    def test_create_remediation_for_nonexistent_gap(self, admin_client):
        """Test POST /api/gap-remediation returns 404 for non-existent gap"""
        fake_id = str(uuid.uuid4())
        
        response = admin_client.post(
            f"{BASE_URL}/api/gap-remediation",
            json={
                "gap_id": fake_id,
                "priority": "HIGH"
            }
        )
        
        assert response.status_code == 404


class TestGapRemediationWorkflow:
    """Tests for gap remediation workflow"""
    
    def test_select_approach_on_draft_remediation(self, admin_client):
        """Test selecting an approach on a draft remediation
        
        BUG: This test fails with 500 error due to missing timedelta import in agents/__init__.py
        Line 1264: target_date = current_date + timedelta(days=target_days)
        NameError: name 'timedelta' is not defined
        """
        # Get remediations
        response = admin_client.get(f"{BASE_URL}/api/gap-remediation")
        remediations = response.json()
        
        draft_remediations = [r for r in remediations if r['status'] == 'DRAFT']
        if len(draft_remediations) == 0:
            pytest.skip("No draft remediations available for testing")
        
        rem = draft_remediations[0]
        
        # Select approach - BUG: Returns 500 due to missing timedelta import
        response = admin_client.put(
            f"{BASE_URL}/api/gap-remediation/{rem['id']}/select-approach?approach=IMPLEMENT"
        )
        
        # This assertion will fail until the bug is fixed
        assert response.status_code == 200, f"BUG: select-approach returns 500 due to missing timedelta import in agents/__init__.py"
        
        # Verify the approach was set
        get_response = admin_client.get(f"{BASE_URL}/api/gap-remediation/{rem['id']}")
        assert get_response.status_code == 200
        updated = get_response.json()
        assert updated['selected_approach'] == 'IMPLEMENT'
    
    def test_endpoints_require_authentication(self, api_client):
        """Test that endpoints require authentication"""
        endpoints = [
            f"{BASE_URL}/api/gap-analysis",
            f"{BASE_URL}/api/gap-remediation"
        ]
        
        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"
