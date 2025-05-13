import json
import pytest
from app import create_app
import os

@pytest.fixture
def auth_headers(client):
    """Get authentication headers"""
    response = client.post('/api/login', 
                          json={
                              'email': os.getenv("TEST_USER_EMAIL"),
                              'password': os.getenv("TEST_USER_PS")
                          })
    data = json.loads(response.data)
    return {'Authorization': f'Bearer {data["access_token"]}'}

def test_get_analytics(client, auth_headers):
    """Test getting analytics data"""
    response = client.get('/api/analytics', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check for expected analytics data structures
    assert 'job_title_distribution' in data
    assert 'experience_level_distribution' in data
    assert 'top_skills' in data
    assert 'education_to_job_title' in data
    
    # Verify structure of education_to_job_title
    assert 'nodes' in data['education_to_job_title']
    assert 'links' in data['education_to_job_title']

def test_get_analytics_without_auth(client):
    """Test getting analytics data without authentication"""
    response = client.get('/api/analytics')
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Missing or invalid Authorization header'