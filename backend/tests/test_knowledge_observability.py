"""
Backend API Integration Tests for Knowledge Graph and Observability
Tests knowledge graph, observability dashboard, and issue management
"""
import pytest
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestKnowledgeGraph:
    """Test knowledge graph endpoints"""
    
    def test_get_knowledge_graph(self, lod1_client):
        """Test getting knowledge graph entities and relations"""
        response = lod1_client.get(f"{BASE_URL}/api/knowledge-graph")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "entities" in data, "Response should contain entities"
        assert "relations" in data, "Response should contain relations"
        assert "stats" in data, "Response should contain stats"
        
        # Verify stats structure
        stats = data["stats"]
        assert "entity_count" in stats
        assert "relation_count" in stats
        assert "entity_types" in stats
    
    def test_get_knowledge_graph_filtered(self, lod1_client):
        """Test getting knowledge graph filtered by entity type"""
        response = lod1_client.get(f"{BASE_URL}/api/knowledge-graph?entity_type=SYSTEM")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # All entities should be of type SYSTEM
        for entity in data["entities"]:
            assert entity["entity_type"] == "SYSTEM"
    
    def test_query_knowledge_graph(self, lod1_client, unique_id):
        """Test querying knowledge graph by entity name"""
        # First create an assessment to populate the graph
        assessment_data = {
            "name": f"TEST_KG_{unique_id}",
            "system_name": f"TEST_KGSystem_{unique_id}",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF"],
            "description": "Test assessment for knowledge graph"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/assessments", json=assessment_data)
        assert create_response.status_code == 200
        
        # Query the knowledge graph
        response = lod1_client.get(f"{BASE_URL}/api/knowledge-graph/query?entity_name=TEST_KGSystem_{unique_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "root_entity" in data
        assert "related_entities" in data
        assert "relations" in data


class TestObservabilityDashboard:
    """Test observability dashboard endpoints"""
    
    def test_get_observability_dashboard(self, lod1_client):
        """Test getting observability dashboard data"""
        response = lod1_client.get(f"{BASE_URL}/api/observability/dashboard")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify model performance section
        assert "model_performance" in data
        model_perf = data["model_performance"]
        assert "total_requests" in model_perf
        assert "total_tokens" in model_perf
        assert "total_cost_usd" in model_perf
        assert "avg_latency_ms" in model_perf
        assert "success_rate" in model_perf
        
        # Verify agent activity section
        assert "agent_activity" in data
        agent_activity = data["agent_activity"]
        assert "total_activities" in agent_activity
        assert "completed" in agent_activity
        assert "failed" in agent_activity
        
        # Verify knowledge graph section
        assert "knowledge_graph" in data
        kg = data["knowledge_graph"]
        assert "total_entities" in kg
        assert "total_relations" in kg
        
        # Verify LLM config section
        assert "llm_config" in data
        llm_config = data["llm_config"]
        assert "provider" in llm_config
        assert "model_name" in llm_config


class TestIssueManagement:
    """Test issue management endpoints"""
    
    def test_create_issue(self, lod1_client, unique_id):
        """Test creating a new issue"""
        issue_data = {
            "title": f"TEST_Issue_{unique_id}",
            "description": "Test issue for automated testing",
            "type": "CONTROL_DEFICIENCY",
            "severity": "HIGH",
            "priority": "P2",
            "source": "Assessment",
            "business_unit": "Technology Risk",
            "frameworks": ["NIST CSF"]
        }
        
        response = lod1_client.post(f"{BASE_URL}/api/issues", json=issue_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "issue_number" in data
        assert data["title"] == issue_data["title"]
        assert data["type"] == issue_data["type"]
        assert data["severity"] == issue_data["severity"]
        assert data["priority"] == issue_data["priority"]
        assert data["status"] == "NEW"
        assert "due_date" in data
        
        return data["id"]
    
    def test_list_issues(self, lod1_client):
        """Test listing issues"""
        response = lod1_client.get(f"{BASE_URL}/api/issues")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
    
    def test_list_issues_filtered(self, lod1_client, unique_id):
        """Test listing issues with filters"""
        # First create an issue
        issue_data = {
            "title": f"TEST_FilterIssue_{unique_id}",
            "description": "Test issue for filter testing",
            "type": "SECURITY_VULNERABILITY",
            "severity": "CRITICAL",
            "priority": "P1",
            "source": "Assessment",
            "business_unit": "Technology Risk"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/issues", json=issue_data)
        assert create_response.status_code == 200
        
        # Filter by status
        response = lod1_client.get(f"{BASE_URL}/api/issues?status=NEW")
        assert response.status_code == 200
        
        # Filter by priority
        response = lod1_client.get(f"{BASE_URL}/api/issues?priority=P1")
        assert response.status_code == 200
    
    def test_get_issue_by_id(self, lod1_client, unique_id):
        """Test getting issue by ID"""
        # First create an issue
        issue_data = {
            "title": f"TEST_GetIssue_{unique_id}",
            "description": "Test issue for get by ID",
            "type": "AUDIT_FINDING",
            "severity": "MEDIUM",
            "priority": "P3",
            "source": "Audit",
            "business_unit": "Compliance"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/issues", json=issue_data)
        assert create_response.status_code == 200
        issue_id = create_response.json()["id"]
        
        # Get the issue by ID
        response = lod1_client.get(f"{BASE_URL}/api/issues/{issue_id}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["id"] == issue_id
        assert data["title"] == issue_data["title"]
    
    def test_update_issue(self, lod1_client, unique_id):
        """Test updating an issue"""
        # First create an issue
        issue_data = {
            "title": f"TEST_UpdateIssue_{unique_id}",
            "description": "Test issue for update",
            "type": "POLICY_VIOLATION",
            "severity": "LOW",
            "priority": "P4",
            "source": "Review",
            "business_unit": "Operations"
        }
        
        create_response = lod1_client.post(f"{BASE_URL}/api/issues", json=issue_data)
        assert create_response.status_code == 200
        issue_id = create_response.json()["id"]
        
        # Update the issue
        update_data = {
            "status": "IN_PROGRESS",
            "progress": 25
        }
        
        response = lod1_client.put(f"{BASE_URL}/api/issues/{issue_id}", json=update_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["status"] == "IN_PROGRESS"
        assert data["progress"] == 25


class TestAnalytics:
    """Test analytics endpoints"""
    
    def test_get_analytics_summary(self, lod1_client):
        """Test getting analytics summary"""
        response = lod1_client.get(f"{BASE_URL}/api/analytics/summary")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "total_assessments" in data
        assert "high_risks" in data
        assert "ineffective_controls" in data
        assert "avg_compliance_score" in data
        assert "frameworks_covered" in data
    
    def test_get_analytics_trends(self, lod1_client):
        """Test getting analytics trends"""
        response = lod1_client.get(f"{BASE_URL}/api/analytics/trends")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "quarters" in data
        assert "risk_scores" in data
        assert "compliance_scores" in data
        assert "assessments_count" in data
