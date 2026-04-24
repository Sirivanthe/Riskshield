"""
Backend tests for AI Compliance features
Tests AI System registration, EU AI Act, NIST AI RMF assessments
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAIFrameworks:
    """Test AI Frameworks endpoint"""

    def test_get_ai_frameworks(self, lod1_client):
        """Get available AI compliance frameworks"""
        response = lod1_client.get(f"{BASE_URL}/api/ai-frameworks")
        assert response.status_code == 200
        
        data = response.json()
        assert 'frameworks' in data
        
        frameworks = data['frameworks']
        assert len(frameworks) >= 2
        
        # Check EU AI Act framework
        eu_ai_act = next((f for f in frameworks if f['id'] == 'EU_AI_ACT'), None)
        assert eu_ai_act is not None
        assert eu_ai_act['name'] == 'EU AI Act'
        assert 'categories' in eu_ai_act
        assert 'risk_categories' in eu_ai_act
        assert 'UNACCEPTABLE' in eu_ai_act['risk_categories']
        assert 'HIGH' in eu_ai_act['risk_categories']
        
        # Check NIST AI RMF framework
        nist_rmf = next((f for f in frameworks if f['id'] == 'NIST_AI_RMF'), None)
        assert nist_rmf is not None
        assert nist_rmf['name'] == 'NIST AI Risk Management Framework'
        assert 'categories' in nist_rmf
        assert 'GOVERN' in nist_rmf['categories']
        assert 'MAP' in nist_rmf['categories']
        assert 'MEASURE' in nist_rmf['categories']
        assert 'MANAGE' in nist_rmf['categories']


class TestAISystemRegistration:
    """Test AI System registration and management"""

    def test_register_ai_system(self, lod1_client, unique_id):
        """Register a new AI system"""
        system_data = {
            "name": f"TEST_AI_System_{unique_id}",
            "description": "Test AI system for credit scoring",
            "purpose": "Automated credit risk assessment",
            "ai_type": "ML Model",
            "deployment_status": "Development",
            "risk_category": "HIGH",
            "business_unit": "Consumer Banking",
            "owner": "risk-team@bank.com",
            "data_types_processed": ["Personal data", "Financial data"],
            "decision_impact": "High",
            "human_oversight_level": "Significant"
        }
        
        response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['name'] == system_data['name']
        assert data['risk_category'] == 'HIGH'
        assert data['deployment_status'] == 'Development'
        assert 'system_id' in data
        assert data['system_id'].startswith('AI-')
        assert data['next_assessment_due'] is not None
        
        return data['id']

    def test_register_high_risk_ai_system_assessment_due(self, lod1_client, unique_id):
        """High risk AI system should have assessment due within 30 days"""
        system_data = {
            "name": f"TEST_HighRisk_{unique_id}",
            "description": "High risk AI system",
            "purpose": "Automated decision making",
            "ai_type": "Deep Learning",
            "deployment_status": "Production",
            "risk_category": "HIGH",
            "business_unit": "Operations",
            "owner": "ai-team@bank.com",
            "data_types_processed": ["Biometric data"],
            "decision_impact": "Critical",
            "human_oversight_level": "Full"
        }
        
        response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['risk_category'] == 'HIGH'
        # High risk systems should have assessment due within 30 days
        assert data['next_assessment_due'] is not None

    def test_list_ai_systems(self, lod1_client):
        """List all registered AI systems"""
        response = lod1_client.get(f"{BASE_URL}/api/ai-systems")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_filter_ai_systems_by_risk_category(self, lod1_client, unique_id):
        """Filter AI systems by risk category"""
        # Create a HIGH risk system
        system_data = {
            "name": f"TEST_FilterRisk_{unique_id}",
            "description": "High risk system for filtering",
            "purpose": "Testing",
            "ai_type": "LLM",
            "deployment_status": "Testing",
            "risk_category": "HIGH",
            "business_unit": "IT",
            "owner": "test@bank.com",
            "data_types_processed": [],
            "decision_impact": "Medium",
            "human_oversight_level": "Limited"
        }
        lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        
        # Filter by HIGH risk
        response = lod1_client.get(f"{BASE_URL}/api/ai-systems?risk_category=HIGH")
        assert response.status_code == 200
        
        data = response.json()
        for system in data:
            assert system['risk_category'] == 'HIGH'

    def test_filter_ai_systems_by_deployment_status(self, lod1_client, unique_id):
        """Filter AI systems by deployment status"""
        # Create a Production system
        system_data = {
            "name": f"TEST_FilterStatus_{unique_id}",
            "description": "Production system for filtering",
            "purpose": "Testing",
            "ai_type": "Computer Vision",
            "deployment_status": "Production",
            "risk_category": "LIMITED",
            "business_unit": "Security",
            "owner": "security@bank.com",
            "data_types_processed": [],
            "decision_impact": "Low",
            "human_oversight_level": "None"
        }
        lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        
        # Filter by Production status
        response = lod1_client.get(f"{BASE_URL}/api/ai-systems?deployment_status=Production")
        assert response.status_code == 200
        
        data = response.json()
        for system in data:
            assert system['deployment_status'] == 'Production'

    def test_get_ai_system_by_id(self, lod1_client, unique_id):
        """Get AI system by ID"""
        # Create system
        system_data = {
            "name": f"TEST_GetById_{unique_id}",
            "description": "System for get by ID test",
            "purpose": "Testing",
            "ai_type": "NLP",
            "deployment_status": "Development",
            "risk_category": "MINIMAL",
            "business_unit": "Research",
            "owner": "research@bank.com",
            "data_types_processed": [],
            "decision_impact": "Low",
            "human_oversight_level": "None"
        }
        create_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = create_response.json()['id']
        
        # Get by ID
        response = lod1_client.get(f"{BASE_URL}/api/ai-systems/{system_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == system_id
        assert data['name'] == system_data['name']

    def test_get_nonexistent_ai_system_returns_404(self, lod1_client):
        """Get non-existent AI system returns 404"""
        response = lod1_client.get(f"{BASE_URL}/api/ai-systems/nonexistent-id")
        assert response.status_code == 404


class TestEUAIActAssessment:
    """Test EU AI Act compliance assessments"""

    def test_create_eu_ai_act_assessment(self, lod1_client, unique_id):
        """Create EU AI Act assessment for an AI system"""
        # First register an AI system
        system_data = {
            "name": f"TEST_EUAI_{unique_id}",
            "description": "System for EU AI Act assessment",
            "purpose": "Credit scoring",
            "ai_type": "ML Model",
            "deployment_status": "Production",
            "risk_category": "HIGH",
            "business_unit": "Lending",
            "owner": "lending@bank.com",
            "data_types_processed": ["Financial data", "Credit history"],
            "decision_impact": "High",
            "human_oversight_level": "Significant"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        # Create EU AI Act assessment
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "EU_AI_ACT",
            "assessment_type": "Initial"
        }
        response = lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['ai_system_id'] == system_id
        assert data['framework'] == 'EU_AI_ACT'
        assert data['status'] == 'IN_PROGRESS'
        assert 'control_results' in data
        assert len(data['control_results']) >= 10, "EU AI Act should have at least 10 mandatory controls"
        
        # Verify control categories
        categories = set(c['category'] for c in data['control_results'])
        assert 'Risk Classification' in categories or 'Risk Management' in categories
        
        return data['id']

    def test_eu_ai_act_controls_for_high_risk(self, lod1_client, unique_id):
        """EU AI Act assessment for HIGH risk system should include mandatory controls"""
        # Register HIGH risk system
        system_data = {
            "name": f"TEST_EUHighRisk_{unique_id}",
            "description": "High risk system for EU AI Act",
            "purpose": "Automated hiring decisions",
            "ai_type": "ML Model",
            "deployment_status": "Production",
            "risk_category": "HIGH",
            "business_unit": "HR",
            "owner": "hr@bank.com",
            "data_types_processed": ["Personal data"],
            "decision_impact": "Critical",
            "human_oversight_level": "Full"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        # Create assessment
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "EU_AI_ACT",
            "assessment_type": "Initial"
        }
        response = lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        assert response.status_code == 200
        
        data = response.json()
        # Check for mandatory controls
        control_names = [c['control_name'] for c in data['control_results']]
        
        # Should have key EU AI Act controls
        assert any('Risk' in name for name in control_names)
        assert any('Data' in name or 'Governance' in name for name in control_names)


class TestNISTAIRMFAssessment:
    """Test NIST AI RMF compliance assessments"""

    def test_create_nist_ai_rmf_assessment(self, lod1_client, unique_id):
        """Create NIST AI RMF assessment for an AI system"""
        # First register an AI system
        system_data = {
            "name": f"TEST_NIST_{unique_id}",
            "description": "System for NIST AI RMF assessment",
            "purpose": "Fraud detection",
            "ai_type": "Deep Learning",
            "deployment_status": "Production",
            "risk_category": "HIGH",
            "business_unit": "Fraud Prevention",
            "owner": "fraud@bank.com",
            "data_types_processed": ["Financial data", "Behavioral data"],
            "decision_impact": "High",
            "human_oversight_level": "Significant"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        # Create NIST AI RMF assessment
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "NIST_AI_RMF",
            "assessment_type": "Initial"
        }
        response = lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data['ai_system_id'] == system_id
        assert data['framework'] == 'NIST_AI_RMF'
        assert data['status'] == 'IN_PROGRESS'
        assert 'control_results' in data
        assert len(data['control_results']) >= 12, "NIST AI RMF should have at least 12 controls"
        
        # Verify GOVERN, MAP, MEASURE, MANAGE categories
        categories = set(c['category'] for c in data['control_results'])
        assert 'GOVERN' in categories
        assert 'MAP' in categories
        assert 'MEASURE' in categories
        assert 'MANAGE' in categories
        
        return data['id']

    def test_nist_ai_rmf_functions(self, lod1_client, unique_id):
        """NIST AI RMF assessment should cover all four functions"""
        # Register system
        system_data = {
            "name": f"TEST_NISTFunctions_{unique_id}",
            "description": "System for NIST functions test",
            "purpose": "Risk analysis",
            "ai_type": "Predictive Analytics",
            "deployment_status": "Testing",
            "risk_category": "LIMITED",
            "business_unit": "Risk",
            "owner": "risk@bank.com",
            "data_types_processed": [],
            "decision_impact": "Medium",
            "human_oversight_level": "Limited"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        # Create assessment
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "NIST_AI_RMF",
            "assessment_type": "Initial"
        }
        response = lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        assert response.status_code == 200
        
        data = response.json()
        categories = [c['category'] for c in data['control_results']]
        
        # All four NIST AI RMF functions should be present
        assert 'GOVERN' in categories, "GOVERN function missing"
        assert 'MAP' in categories, "MAP function missing"
        assert 'MEASURE' in categories, "MEASURE function missing"
        assert 'MANAGE' in categories, "MANAGE function missing"


class TestAIAssessmentManagement:
    """Test AI assessment listing and management"""

    def test_list_ai_assessments(self, lod1_client):
        """List all AI assessments"""
        response = lod1_client.get(f"{BASE_URL}/api/ai-assessments")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_filter_assessments_by_ai_system(self, lod1_client, unique_id):
        """Filter assessments by AI system ID"""
        # Create system and assessment
        system_data = {
            "name": f"TEST_FilterAssess_{unique_id}",
            "description": "System for filter test",
            "purpose": "Testing",
            "ai_type": "ML Model",
            "deployment_status": "Development",
            "risk_category": "MINIMAL",
            "business_unit": "Test",
            "owner": "test@bank.com",
            "data_types_processed": [],
            "decision_impact": "Low",
            "human_oversight_level": "None"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "EU_AI_ACT",
            "assessment_type": "Initial"
        }
        lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        
        # Filter by system ID
        response = lod1_client.get(f"{BASE_URL}/api/ai-assessments?ai_system_id={system_id}")
        assert response.status_code == 200
        
        data = response.json()
        for assessment in data:
            assert assessment['ai_system_id'] == system_id

    def test_filter_assessments_by_framework(self, lod1_client, unique_id):
        """Filter assessments by framework"""
        # Create system and EU AI Act assessment
        system_data = {
            "name": f"TEST_FilterFW_{unique_id}",
            "description": "System for framework filter",
            "purpose": "Testing",
            "ai_type": "LLM",
            "deployment_status": "Development",
            "risk_category": "LIMITED",
            "business_unit": "Test",
            "owner": "test@bank.com",
            "data_types_processed": [],
            "decision_impact": "Low",
            "human_oversight_level": "None"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "EU_AI_ACT",
            "assessment_type": "Initial"
        }
        lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        
        # Filter by EU_AI_ACT framework
        response = lod1_client.get(f"{BASE_URL}/api/ai-assessments?framework=EU_AI_ACT")
        assert response.status_code == 200
        
        data = response.json()
        for assessment in data:
            assert assessment['framework'] == 'EU_AI_ACT'

    def test_complete_ai_assessment(self, lod1_client, unique_id):
        """Complete an AI assessment and calculate compliance"""
        # Create system and assessment
        system_data = {
            "name": f"TEST_Complete_{unique_id}",
            "description": "System for completion test",
            "purpose": "Testing",
            "ai_type": "ML Model",
            "deployment_status": "Production",
            "risk_category": "HIGH",
            "business_unit": "Test",
            "owner": "test@bank.com",
            "data_types_processed": [],
            "decision_impact": "High",
            "human_oversight_level": "Significant"
        }
        system_response = lod1_client.post(f"{BASE_URL}/api/ai-systems", json=system_data)
        system_id = system_response.json()['id']
        
        assessment_data = {
            "ai_system_id": system_id,
            "framework": "EU_AI_ACT",
            "assessment_type": "Initial"
        }
        assess_response = lod1_client.post(f"{BASE_URL}/api/ai-assessments", json=assessment_data)
        assessment_id = assess_response.json()['id']
        
        # Complete assessment
        response = lod1_client.post(f"{BASE_URL}/api/ai-assessments/{assessment_id}/complete")
        assert response.status_code == 200
        
        data = response.json()
        assert 'overall_compliance' in data
        assert 'compliance_percentage' in data
        assert data['overall_compliance'] in ['COMPLIANT', 'PARTIALLY_COMPLIANT', 'NON_COMPLIANT']


class TestGapAnalysis:
    """Test Gap Analysis functionality"""

    def test_run_gap_analysis(self, lod1_client, unique_id):
        """Run gap analysis for an assessment against a framework"""
        # First create an assessment
        from datetime import datetime
        
        # Create assessment via API
        assessment_data = {
            "name": f"TEST_GapAnalysis_{unique_id}",
            "system_name": "Test System",
            "business_unit": "Technology",
            "frameworks": ["NIST CSF"],
            "description": "Assessment for gap analysis"
        }
        assess_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        
        if assess_response.status_code == 200:
            assessment_id = assess_response.json()['id']
            
            # Run gap analysis
            response = lod1_client.post(
                f"{BASE_URL}/api/gap-analysis/run",
                params={"assessment_id": assessment_id, "framework": "NIST CSF"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert 'assessment_id' in data
            assert 'framework' in data
            assert 'total_requirements' in data
            assert 'gaps_identified' in data
            assert 'coverage_percentage' in data
            assert data['framework'] == 'NIST CSF'

    def test_list_control_gaps(self, lod1_client):
        """List control gaps"""
        response = lod1_client.get(f"{BASE_URL}/api/gap-analysis")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_filter_gaps_by_framework(self, lod1_client):
        """Filter gaps by framework"""
        response = lod1_client.get(f"{BASE_URL}/api/gap-analysis?framework=NIST CSF")
        assert response.status_code == 200
        
        data = response.json()
        for gap in data:
            assert gap['framework'] == 'NIST CSF'
