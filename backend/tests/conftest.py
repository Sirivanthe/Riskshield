import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def lod1_token():
    """Get LOD1 authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "lod1@bank.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("LOD1 authentication failed — skipping authenticated tests")

@pytest.fixture
def lod2_token():
    """Get LOD2 authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "lod2@bank.com",
        "password": "password123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("LOD2 authentication failed — skipping authenticated tests")

@pytest.fixture
def admin_token():
    """Get Admin authentication token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@bank.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed — skipping authenticated tests")

@pytest.fixture
def lod1_client(lod1_token):
    """Session with LOD1 auth header - separate session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {lod1_token}"
    })
    return session

@pytest.fixture
def lod2_client(lod2_token):
    """Session with LOD2 auth header - separate session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {lod2_token}"
    })
    return session

@pytest.fixture
def admin_client(admin_token):
    """Session with Admin auth header - separate session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}"
    })
    return session

@pytest.fixture
def unique_id():
    """Generate unique ID for test data"""
    return f"TEST_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%H%M%S')}"
