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

def test_get_users(client, auth_headers):
    """Test getting all users"""
    response = client.get('/api/users', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'data' in data
    assert isinstance(data['data'], list)

def test_create_user(client, auth_headers):
    """Test creating a new user"""
    # First, we need to ensure the test user doesn't exist or is deleted
    # This is a simplified approach - in a real test, you might want to clean up after
    
    # Generate a unique email to avoid conflicts
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    response = client.post('/api/users', 
                          headers=auth_headers,
                          json={
                              'name': 'Test User',
                              'email': unique_email,
                              'password': 'testpassword123'
                          })
    
    # If user already exists but is deleted, it will return 200
    # If it's a new user, it will return 201
    assert response.status_code in [200, 201]
    data = json.loads(response.data)
    assert 'data' in data
    assert data['data']['email'] == unique_email

def test_get_myself(client, auth_headers):
    """Test getting current user information"""
    response = client.get('/api/users/myself', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['email'] == 'ayusudi.abc@gmail.com'

def test_delete_user(client, auth_headers):
    """Test deleting a user (requires a user ID)"""
    # First, create a test user
    import uuid
    unique_email = f"delete_{uuid.uuid4().hex[:8]}@example.com"
    
    create_response = client.post('/api/users', 
                                 headers=auth_headers,
                                 json={
                                     'name': 'Delete Test User',
                                     'email': unique_email,
                                     'password': 'testpassword123'
                                 })
    
    # Get the user list to find the ID of our test user
    users_response = client.get('/api/users', headers=auth_headers)
    users_data = json.loads(users_response.data)
    
    # Find our test user
    test_user = next((user for user in users_data['data'] if user['email'] == unique_email), None)
    
    if test_user:
        # Now delete the user
        delete_response = client.delete(f'/api/users/{test_user["id"]}', headers=auth_headers)
        assert delete_response.status_code == 200
        data = json.loads(delete_response.data)
        assert 'message' in data