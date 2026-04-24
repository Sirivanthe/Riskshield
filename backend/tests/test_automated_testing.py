"""
Backend integration tests for Automated Testing API endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAutomatedTestingAPI:
    """Tests for /api/automated-tests/* endpoints"""
    
    def test_get_test_runs_returns_list(self, admin_client):
        """Test GET /api/automated-tests/runs returns a list"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/runs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_test_runs_structure(self, admin_client):
        """Test that test runs have expected structure"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/runs")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            run = data[0]
            # Check required fields
            assert 'id' in run
            assert 'run_id' in run
            assert 'control_id' in run
            assert 'control_name' in run
            assert 'test_type' in run
            assert 'status' in run
            assert 'started_at' in run
    
    def test_get_test_types_returns_list(self, admin_client):
        """Test GET /api/automated-tests/test-types returns test types"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/test-types")
        
        assert response.status_code == 200
        data = response.json()
        assert 'test_types' in data
        assert isinstance(data['test_types'], list)
        assert len(data['test_types']) > 0
    
    def test_get_test_types_structure(self, admin_client):
        """Test that test types have expected structure"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/test-types")
        
        assert response.status_code == 200
        data = response.json()
        
        for test_type in data['test_types']:
            assert 'id' in test_type
            assert 'name' in test_type
            assert 'description' in test_type
    
    def test_get_test_types_contains_expected_types(self, admin_client):
        """Test that expected test types are present"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/test-types")
        
        assert response.status_code == 200
        data = response.json()
        
        type_ids = [t['id'] for t in data['test_types']]
        expected_types = ['CONFIGURATION_CHECK', 'ACCESS_REVIEW', 'VULNERABILITY_SCAN', 'AI_BIAS_CHECK']
        
        for expected in expected_types:
            assert expected in type_ids, f"Expected test type {expected} not found"
    
    def test_get_evidence_sources_returns_list(self, admin_client):
        """Test GET /api/automated-tests/evidence-sources returns sources"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/evidence-sources")
        
        assert response.status_code == 200
        data = response.json()
        assert 'sources' in data
        assert isinstance(data['sources'], list)
        assert len(data['sources']) > 0
    
    def test_get_evidence_sources_structure(self, admin_client):
        """Test that evidence sources have expected structure"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/evidence-sources")
        
        assert response.status_code == 200
        data = response.json()
        
        for source in data['sources']:
            assert 'id' in source
            assert 'name' in source
            assert 'type' in source
            assert 'description' in source
    
    def test_get_evidence_sources_contains_expected_sources(self, admin_client):
        """Test that expected evidence sources are present"""
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/evidence-sources")
        
        assert response.status_code == 200
        data = response.json()
        
        source_ids = [s['id'] for s in data['sources']]
        expected_sources = ['AWS_CONFIG', 'AZURE_POLICY', 'IAM_EXPORT', 'VULNERABILITY_SCANNER']
        
        for expected in expected_sources:
            assert expected in source_ids, f"Expected evidence source {expected} not found"
    
    def test_get_test_run_by_id_not_found(self, admin_client):
        """Test GET /api/automated-tests/runs/{run_id} returns 404 for non-existent run"""
        fake_id = str(uuid.uuid4())
        response = admin_client.get(f"{BASE_URL}/api/automated-tests/runs/{fake_id}")
        
        assert response.status_code == 404
    
    def test_run_test_control_not_found(self, admin_client):
        """Test POST /api/automated-tests/run/{control_id} returns 404 for non-existent control"""
        fake_id = str(uuid.uuid4())
        response = admin_client.post(f"{BASE_URL}/api/automated-tests/run/{fake_id}?test_type=CONFIGURATION_CHECK")
        
        assert response.status_code == 404
    
    def test_endpoints_require_authentication(self, api_client):
        """Test that endpoints require authentication"""
        endpoints = [
            f"{BASE_URL}/api/automated-tests/runs",
            f"{BASE_URL}/api/automated-tests/test-types",
            f"{BASE_URL}/api/automated-tests/evidence-sources"
        ]
        
        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"


class TestAutomatedTestRunWorkflow:
    """Tests for running automated tests on controls"""
    
    def test_run_test_on_approved_control(self, admin_client):
        """Test running an automated test on an approved control"""
        # First get approved controls
        controls_response = admin_client.get(f"{BASE_URL}/api/controls/library?status=APPROVED")
        if controls_response.status_code != 200:
            pytest.skip("No controls endpoint available")
        
        controls = controls_response.json()
        if len(controls) == 0:
            pytest.skip("No approved controls available for testing")
        
        control = controls[0]
        control_id = control['id']
        
        # Run a test
        response = admin_client.post(
            f"{BASE_URL}/api/automated-tests/run/{control_id}?test_type=CONFIGURATION_CHECK"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'test_run_id' in data
        assert 'run_id' in data
        assert 'status' in data
        assert 'effectiveness_rating' in data
        assert 'confidence_score' in data
        assert data['status'] == 'COMPLETED'
    
    def test_run_test_returns_findings(self, admin_client):
        """Test that running a test returns findings and recommendations"""
        # Get approved controls
        controls_response = admin_client.get(f"{BASE_URL}/api/controls/library?status=APPROVED")
        if controls_response.status_code != 200:
            pytest.skip("No controls endpoint available")
        
        controls = controls_response.json()
        if len(controls) == 0:
            pytest.skip("No approved controls available for testing")
        
        control = controls[0]
        
        # Run a test
        response = admin_client.post(
            f"{BASE_URL}/api/automated-tests/run/{control['id']}?test_type=ACCESS_REVIEW"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify findings and recommendations are present
        assert 'findings' in data
        assert 'recommendations' in data
        assert isinstance(data['findings'], list)
        assert isinstance(data['recommendations'], list)
