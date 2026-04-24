"""
Backend API Integration Tests for Authentication
Tests login with LOD1, LOD2, and Admin users
"""
import pytest
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_lod1_user(self, api_client):
        """Test login with LOD1 user credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lod1@bank.com",
            "password": "password123"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["email"] == "lod1@bank.com"
        assert data["user"]["role"] == "LOD1_USER"
        assert data["token_type"] == "bearer"
    
    def test_login_lod2_user(self, api_client):
        """Test login with LOD2 user credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lod2@bank.com",
            "password": "password123"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["email"] == "lod2@bank.com"
        assert data["user"]["role"] == "LOD2_USER"
    
    def test_login_admin_user(self, api_client):
        """Test login with Admin user credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@bank.com",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "access_token" in data
        assert data["user"]["email"] == "admin@bank.com"
        assert data["user"]["role"] == "ADMIN"
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials returns 401"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@bank.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_login_wrong_password(self, api_client):
        """Test login with wrong password returns 401"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lod1@bank.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_get_current_user(self, lod1_client):
        """Test getting current user info with valid token"""
        response = lod1_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["email"] == "lod1@bank.com"
        assert data["role"] == "LOD1_USER"
        assert "id" in data
        assert "full_name" in data
    
    def test_get_current_user_unauthorized(self, api_client):
        """Test getting current user without token returns 403"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    def test_get_current_user_invalid_token(self, api_client):
        """Test getting current user with invalid token returns 401"""
        api_client.headers.update({"Authorization": "Bearer invalid_token"})
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
