import json
import pytest
from app import create_app
import os

def test_login_success(client):
    """Test successful login with valid credentials"""
    response = client.post('/api/login', 
                          json={
                              'email': os.environ.get('TEST_USER_EMAIL'),
                              'password': os.environ.get('TEST_USER_PS')
                          })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == os.environ.get('TEST_USER_EMAIL')

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/api/login', 
                          json={
                              'email': 'wronguserc@gmail.com',
                              'password': 'wrongpassword'
                          })
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post('/api/login', 
                          json={
                              'email': 'sample@gmail.com'
                          })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data