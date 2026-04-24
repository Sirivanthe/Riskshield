"""
Backend API Integration Tests for Assessments
Tests assessment creation, retrieval, and multi-agent processing
"""
import pytest
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAssessments:
    """Test assessment endpoints"""
    
    def test_list_assessments_empty(self, lod1_client):
        """Test listing assessments (may be empty initially)"""
        response = lod1_client.get(f"{BASE_URL}/api/assessments")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
    
    def test_create_assessment(self, lod1_client, unique_id):
        """Test creating a new assessment with multi-agent processing"""
        assessment_data = {
            "name": f"TEST_Assessment_{unique_id}",
            "system_name": f"TEST_System_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF", "ISO 27001"],
            "description": "Test assessment for automated testing",
            "scenario": "Test scenario"
        }
        
        response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify assessment structure
        assert "id" in data, "Response should contain id"
        assert data["name"] == assessment_data["name"]
        assert data["system_name"] == assessment_data["system_name"]
        assert data["business_unit"] == assessment_data["business_unit"]
        assert data["frameworks"] == assessment_data["frameworks"]
        
        # Verify multi-agent processing results
        assert data["status"] == "COMPLETED", f"Assessment should be COMPLETED, got {data['status']}"
        assert "risks" in data, "Assessment should contain risks"
        assert "controls" in data, "Assessment should contain controls"
        assert "evidence" in data, "Assessment should contain evidence"
        assert "summary" in data, "Assessment should contain summary"
        
        # Verify risks were identified
        assert len(data["risks"]) > 0, "Should have identified at least one risk"
        for risk in data["risks"]:
            assert "title" in risk
            assert "severity" in risk
            assert risk["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        # Verify controls were tested
        assert len(data["controls"]) > 0, "Should have tested at least one control"
        for control in data["controls"]:
            assert "name" in control
            assert "effectiveness" in control
            assert control["effectiveness"] in ["EFFECTIVE", "PARTIALLY_EFFECTIVE", "INEFFECTIVE", "NOT_TESTED"]
        
        # Verify summary
        assert "overall_score" in data["summary"]
        assert "risk_summary" in data["summary"]
        assert "control_summary" in data["summary"]
        
        return data["id"]
    
    def test_get_assessment_by_id(self, lod1_client, unique_id):
        """Test getting assessment by ID"""
        # First create an assessment
        assessment_data = {
            "name": f"TEST_GetById_{unique_id}",
            "system_name": f"TEST_System_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF"],
            "description": "Test assessment for get by ID"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Get the assessment by ID
        response = lod1_client.get(f"{BASE_URL}/api/assessments/{created_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["id"] == created_id
        assert data["name"] == assessment_data["name"]
    
    def test_get_assessment_not_found(self, lod1_client):
        """Test getting non-existent assessment returns 404"""
        response = lod1_client.get(f"{BASE_URL}/api/assessments/non-existent-id")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_list_assessments_after_creation(self, lod1_client, unique_id):
        """Test that created assessment appears in list"""
        # Create an assessment
        assessment_data = {
            "name": f"TEST_ListCheck_{unique_id}",
            "system_name": f"TEST_System_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["SOC2"],
            "description": "Test assessment for list check"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # List assessments
        list_response = lod1_client.get(f"{BASE_URL}/api/assessments")
        assert list_response.status_code == 200
        
        assessments = list_response.json()
        assessment_ids = [a["id"] for a in assessments]
        
        assert created_id in assessment_ids, "Created assessment should appear in list"


class TestAgentActivity:
    """Test agent activity tracking endpoints"""
    
    def test_get_agent_activities(self, lod1_client, unique_id):
        """Test getting agent activities for a session"""
        # First create an assessment to generate activities
        assessment_data = {
            "name": f"TEST_Activities_{unique_id}",
            "system_name": f"TEST_System_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF"],
            "description": "Test assessment for activity tracking"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]
        
        # Get activities for this session
        response = lod1_client.get(f"{BASE_URL}/api/agent-activities/{session_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        activities = response.json()
        
        assert isinstance(activities, list), "Response should be a list"
        assert len(activities) > 0, "Should have recorded activities"
        
        # Verify activity structure
        for activity in activities:
            assert "agent_name" in activity
            assert "activity_type" in activity
            assert "status" in activity
            assert activity["status"] in ["RUNNING", "COMPLETED", "FAILED", "WAITING"]


class TestModelMetrics:
    """Test model metrics endpoints"""
    
    def test_get_model_metrics(self, lod1_client, unique_id):
        """Test getting model metrics for a session"""
        # First create an assessment to generate metrics
        assessment_data = {
            "name": f"TEST_Metrics_{unique_id}",
            "system_name": f"TEST_System_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF"],
            "description": "Test assessment for metrics"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]
        
        # Get metrics for this session
        response = lod1_client.get(f"{BASE_URL}/api/model-metrics/{session_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "metrics" in data, "Response should contain metrics"
        assert "summary" in data, "Response should contain summary"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_requests" in summary
        assert "total_tokens" in summary
        assert "total_cost_usd" in summary
        assert "avg_latency_ms" in summary


class TestExplanations:
    """Test AI explanations endpoints"""
    
    def test_get_explanations(self, lod1_client, unique_id):
        """Test getting AI explanations for a session"""
        # First create an assessment to generate explanations
        assessment_data = {
            "name": f"TEST_Explanations_{unique_id}",
            "system_name": f"TEST_System_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF"],
            "description": "Test assessment for explanations"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]
        
        # Get explanations for this session
        response = lod1_client.get(f"{BASE_URL}/api/explanations/{session_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        explanations = response.json()
        
        assert isinstance(explanations, list), "Response should be a list"
        assert len(explanations) > 0, "Should have recorded explanations"
        
        # Verify explanation structure
        for explanation in explanations:
            assert "explanation_type" in explanation
            assert "entity_name" in explanation
            assert "reasoning" in explanation
            assert "confidence_score" in explanation
