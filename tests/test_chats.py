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

def test_create_chat(client, auth_headers):
    """Test creating a new chat"""
    chat_data = {
        'title': 'Test Chat',
        'chats': [
            {'role': 'user', 'content': 'Hello, this is a test message'},
            {'role': 'assistant', 'content': 'This is a test response'}
        ]
    }
    
    response = client.post('/api/chats', 
                          headers=auth_headers,
                          json=chat_data)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    
    # Return the chat data for use in other tests
    return chat_data

def test_get_chats(client, auth_headers):
    """Test getting all chats"""
    # First create a chat
    test_create_chat(client, auth_headers)
    
    # Now get all chats
    response = client.get('/api/chats', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'chats' in data
    assert isinstance(data['chats'], list)
    assert len(data['chats']) > 0

def test_get_chat_by_id(client, auth_headers):
    """Test getting a chat by ID"""
    # First create a chat
    test_create_chat(client, auth_headers)
    
    # Get all chats to find the ID
    chats_response = client.get('/api/chats', headers=auth_headers)
    chats_data = json.loads(chats_response.data)
    
    if len(chats_data['chats']) > 0:
        chat_id = chats_data['chats'][0]['id']
        
        # Now get the specific chat
        response = client.get(f'/api/chats/{chat_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'chat' in data
        assert data['chat']['id'] == chat_id

def test_create_chat_without_auth(client):
    """Test creating a new chat without authentication"""
    chat_data = {
        'title': 'Test Chat',
        'chats': [
            {'role': 'user', 'content': 'Hello, this is a test message'},
            {'role': 'assistant', 'content': 'This is a test response'}
        ]
    }
    
    response = client.post('/api/chats', json=chat_data)
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Missing or invalid Authorization header'
   
def test_get_chats_without_auth(client):
    """Test getting all chats without authentication"""
    response = client.get('/api/chats')
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'Missing or invalid Authorization header'

def test_get_chat_by_invalid_id(client, auth_headers):
    """Test getting a chat with an invalid ID"""
    # Use a non-existent ID
    invalid_id = 9999
    
    response = client.get(f'/api/chats/{invalid_id}', headers=auth_headers)
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert 'not found' in data['error'].lower()