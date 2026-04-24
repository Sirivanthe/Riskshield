"""
Backend API Integration Tests for LLM Configuration
Tests LLM config, providers, and connection testing
"""
import pytest
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestLLMConfiguration:
    """Test LLM configuration endpoints"""
    
    def test_get_llm_config(self, lod1_client):
        """Test getting current LLM configuration"""
        response = lod1_client.get(f"{BASE_URL}/api/llm/config")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "provider" in data, "Response should contain provider"
        assert "model_name" in data, "Response should contain model_name"
        assert "temperature" in data, "Response should contain temperature"
        assert "max_tokens" in data, "Response should contain max_tokens"
        # Default provider should be MOCK
        assert data["provider"] in ["MOCK", "OLLAMA", "AZURE", "VERTEX_AI"]
    
    def test_list_llm_providers(self, lod1_client):
        """Test listing available LLM providers"""
        response = lod1_client.get(f"{BASE_URL}/api/llm/providers")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "providers" in data, "Response should contain providers array"
        providers = data["providers"]
        
        assert len(providers) >= 4, "Should have at least 4 providers"
        
        provider_ids = [p["id"] for p in providers]
        assert "MOCK" in provider_ids, "Should include MOCK provider"
        assert "OLLAMA" in provider_ids, "Should include OLLAMA provider"
        assert "AZURE" in provider_ids, "Should include AZURE provider"
        assert "VERTEX_AI" in provider_ids, "Should include VERTEX_AI provider"
        
        # Check provider structure
        for provider in providers:
            assert "id" in provider
            assert "name" in provider
            assert "description" in provider
    
    def test_update_llm_config_lod2(self, lod2_client):
        """Test updating LLM configuration as LOD2 user"""
        # First get current config
        get_response = lod2_client.get(f"{BASE_URL}/api/llm/config")
        original_config = get_response.json()
        
        # Update config
        update_data = {
            "provider": "MOCK",
            "model_name": "test-model",
            "temperature": 0.5
        }
        response = lod2_client.put(f"{BASE_URL}/api/llm/config", json=update_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["model_name"] == "test-model"
        assert data["temperature"] == 0.5
        
        # Restore original config
        restore_data = {
            "provider": original_config["provider"],
            "model_name": original_config["model_name"],
            "temperature": original_config["temperature"]
        }
        lod2_client.put(f"{BASE_URL}/api/llm/config", json=restore_data)
    
    def test_update_llm_config_admin(self, admin_client):
        """Test updating LLM configuration as Admin user"""
        update_data = {
            "provider": "MOCK",
            "model_name": "admin-test-model"
        }
        response = admin_client.put(f"{BASE_URL}/api/llm/config", json=update_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["model_name"] == "admin-test-model"
        
        # Restore default
        admin_client.put(f"{BASE_URL}/api/llm/config", json={"model_name": "llama-3-70b"})
    
    def test_update_llm_config_lod1_forbidden(self, lod1_client):
        """Test that LOD1 user cannot update LLM configuration"""
        update_data = {
            "provider": "MOCK",
            "model_name": "should-not-work"
        }
        response = lod1_client.put(f"{BASE_URL}/api/llm/config", json=update_data)
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_llm_health_check(self, lod1_client):
        """Test LLM health check endpoint"""
        response = lod1_client.get(f"{BASE_URL}/api/llm/health")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "provider" in data
        assert "healthy" in data
        assert "timestamp" in data
    
    def test_llm_test_connection(self, lod1_client):
        """Test LLM connection test endpoint"""
        response = lod1_client.post(f"{BASE_URL}/api/llm/test?prompt=Hello")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "success" in data
        assert "provider" in data
        # With MOCK provider, should always succeed
        if data["provider"] == "MOCK":
            assert data["success"] == True
