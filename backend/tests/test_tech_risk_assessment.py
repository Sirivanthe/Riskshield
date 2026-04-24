"""
Tech Risk Assessment API Integration Tests
Tests for the tech risk assessment module with intelligent questionnaire
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestTechRiskAssessmentAPI:
    """Integration tests for Tech Risk Assessment endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, admin_token):
        """Setup for each test."""
        self.client = api_client
        self.token = admin_token
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        self.created_assessments = []
    
    def teardown_method(self):
        """Cleanup created test data."""
        # Note: No delete endpoint available, assessments will remain
        pass
    
    def test_list_assessments(self):
        """Test listing tech risk assessments."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "assessments" in data
        assert isinstance(data["assessments"], list)
    
    def test_create_assessment_with_context(self):
        """Test creating a new tech risk assessment with context."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "app_name": f"TEST_App_{unique_id}",
            "description": "Test application for risk assessment",
            "business_unit": "Technology",
            "context": {
                "data_classification": "CONFIDENTIAL",
                "deployment_type": "CLOUD",
                "internet_facing": True,
                "processes_pii": True,
                "processes_financial_data": False,
                "criticality": "HIGH"
            }
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/tech-risk/assessments?assessor_id=test-user&assessor_name=Test%20User",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "assessment_id" in data
        assert data["app_name"] == payload["app_name"]
        assert data["status"] == "DRAFT"
        assert "context" in data
        assert data["context"]["data_classification"] == "CONFIDENTIAL"
        
        self.created_assessments.append(data["id"])
        return data
    
    def test_get_assessment_by_id(self):
        """Test getting assessment details by ID."""
        # First create an assessment
        assessment = self.test_create_assessment_with_context()
        
        # Then fetch it
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments/{assessment['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == assessment["id"]
        assert data["app_name"] == assessment["app_name"]
    
    def test_get_assessment_not_found(self):
        """Test getting non-existent assessment returns 404."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments/non-existent-id")
        assert response.status_code == 404
    
    def test_get_intelligent_questionnaire(self):
        """Test getting intelligent questionnaire based on context."""
        # Create assessment first
        assessment = self.test_create_assessment_with_context()
        
        # Get questionnaire
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments/{assessment['id']}/questions")
        assert response.status_code == 200
        data = response.json()
        
        # Verify questionnaire structure
        assert "assessment_id" in data
        assert "total_questions" in data
        assert "sections" in data
        assert data["total_questions"] > 0
        
        # Verify sections exist
        expected_sections = ["General Information", "Data Security", "Access Control", "Infrastructure"]
        for section in expected_sections:
            assert section in data["sections"]
    
    def test_submit_questionnaire_and_identify_risks(self):
        """Test submitting questionnaire and getting risk identification."""
        # Create assessment
        assessment = self.test_create_assessment_with_context()
        
        # Submit questionnaire with responses that should trigger risks
        responses = {
            "q1": "Payment processing",
            "q2": "Internal users",
            "q3": "Critical - Major financial/reputational impact",
            "q4": ["PII", "Financial Data"],
            "q5": "Cloud storage",
            "q6": "Only in transit",  # Should trigger encryption risk
            "q7": ["Password only"],  # Should trigger auth risk
            "q8": "Manual process",
            "q9": "No separate management",  # Should trigger PAM risk
            "q10": "None",  # Should trigger DR risk
            "q11": "4 hours",
            "q13": ["PCI-DSS", "SOC2"],
            "q16": "Yes, critical dependencies",
            "q17": "No",  # Should trigger third-party risk
            "q18": "No formal process",  # Should trigger change mgmt risk
            "q19": "Weekly"
        }
        
        response = self.client.post(
            f"{BASE_URL}/api/tech-risk/assessments/{assessment['id']}/questionnaire",
            json={"responses": responses}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify risk identification
        assert "risks_identified" in data
        assert "controls_recommended" in data
        assert "overall_risk_rating" in data
        assert data["risks_identified"] > 0
        assert data["controls_recommended"] > 0
        assert data["status"] == "PENDING_REVIEW"
    
    def test_download_pdf_report(self):
        """Test downloading PDF report for assessment."""
        # Get existing assessment with risks
        list_response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments?status=PENDING_REVIEW")
        assessments = list_response.json().get("assessments", [])
        
        if not assessments:
            pytest.skip("No assessments with PENDING_REVIEW status available")
        
        assessment_id = assessments[0]["id"]
        
        # Download report
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments/{assessment_id}/report")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 1000  # PDF should have substantial content
    
    def test_create_issues_from_risks(self):
        """Test creating issues from identified risks."""
        # Get existing assessment with risks
        list_response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments?status=PENDING_REVIEW")
        assessments = list_response.json().get("assessments", [])
        
        if not assessments:
            pytest.skip("No assessments with risks available")
        
        assessment = assessments[0]
        if not assessment.get("identified_risks"):
            pytest.skip("Assessment has no identified risks")
        
        # Create issues from first risk only
        risk_id = assessment["identified_risks"][0]["risk_id"]
        
        response = self.client.post(
            f"{BASE_URL}/api/tech-risk/assessments/{assessment['id']}/create-issues?creator_id=test-user&creator_name=Test%20User",
            json={"risk_ids": [risk_id]}
        )
        
        # May return 200 even if issues already exist
        assert response.status_code == 200
        data = response.json()
        assert "issues_created" in data
    
    def test_get_risk_categories(self):
        """Test getting available risk categories."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/risk-categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        categories = data["categories"]
        assert len(categories) > 0
        
        # Verify expected categories
        category_ids = [c["id"] for c in categories]
        assert "SECURITY" in category_ids
        assert "ACCESS_CONTROL" in category_ids
        assert "DATA_INTEGRITY" in category_ids
    
    def test_get_risk_ratings(self):
        """Test getting risk rating definitions."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/risk-ratings")
        assert response.status_code == 200
        data = response.json()
        
        assert "ratings" in data
        assert "likelihood_scale" in data
        assert "impact_scale" in data
        
        # Verify ratings
        rating_ids = [r["id"] for r in data["ratings"]]
        assert "CRITICAL" in rating_ids
        assert "HIGH" in rating_ids
        assert "MEDIUM" in rating_ids
        assert "LOW" in rating_ids
    
    def test_get_cmdb_context(self):
        """Test fetching CMDB context (mock data)."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/cmdb/test-cmdb-id")
        assert response.status_code == 200
        data = response.json()
        
        assert "cmdb_id" in data
        assert "context" in data
        # Mock CMDB returns predefined data
        assert data["context"]["app_name"] == "Payment Gateway"
    
    def test_update_assessment_context(self):
        """Test updating assessment context."""
        # Create assessment
        assessment = self.test_create_assessment_with_context()
        
        # Update context
        new_context = {
            "app_name": assessment["app_name"],
            "description": "Updated description",
            "data_classification": "RESTRICTED",
            "deployment_type": "HYBRID",
            "internet_facing": False,
            "criticality": "CRITICAL"
        }
        
        response = self.client.put(
            f"{BASE_URL}/api/tech-risk/assessments/{assessment['id']}/context",
            json={"context": new_context}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify update
        assert data["context"]["data_classification"] == "RESTRICTED"
        assert data["context"]["criticality"] == "CRITICAL"
    
    def test_complete_assessment(self):
        """Test completing an assessment."""
        # Get assessment in PENDING_REVIEW status
        list_response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments?status=PENDING_REVIEW")
        assessments = list_response.json().get("assessments", [])
        
        if not assessments:
            pytest.skip("No assessments in PENDING_REVIEW status")
        
        assessment_id = assessments[0]["id"]
        
        response = self.client.post(
            f"{BASE_URL}/api/tech-risk/assessments/{assessment_id}/complete?reviewer_id=test-reviewer&reviewer_name=Test%20Reviewer&review_comments=Approved"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "COMPLETED"
        assert data["reviewed_by"] == "Test Reviewer"
    
    def test_filter_assessments_by_status(self):
        """Test filtering assessments by status."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments?status=DRAFT")
        assert response.status_code == 200
        data = response.json()
        
        # All returned assessments should have DRAFT status
        for assessment in data["assessments"]:
            assert assessment["status"] == "DRAFT"
    
    def test_filter_assessments_by_app_name(self):
        """Test filtering assessments by application name."""
        response = self.client.get(f"{BASE_URL}/api/tech-risk/assessments?app_name=Payment")
        assert response.status_code == 200
        data = response.json()
        
        # All returned assessments should contain "Payment" in app_name
        for assessment in data["assessments"]:
            assert "payment" in assessment["app_name"].lower()
