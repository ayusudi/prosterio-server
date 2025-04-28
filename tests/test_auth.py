import json
from unittest.mock import patch
import bcrypt

def test_login_without_credentials(client):
    response = client.post('/api/login', headers={'Content-Type': 'application/json'}, json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_login_with_invalid_credentials(client):
    response = client.post('/api/login', headers={'Content-Type': 'application/json'}, json={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_login_success(client):
    test_user = {
        'id': 1,
        'name': 'Test User',
        'email': 'test@example.com',
        'password': bcrypt.hashpw('testpass123'.encode('utf-8'), bcrypt.gensalt()),
        'role': 'HR'
    }
    
    with patch('app.routes.auth.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = [
            test_user['id'],
            test_user['name'],
            test_user['email'],
            test_user['password'],
            test_user['role']
        ]
        
        response = client.post('/api/login',
                             headers={'Content-Type': 'application/json'},
                             json={
                                 'email': test_user['email'],
                                 'password': 'testpass123'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['id'] == test_user['id']
        assert data['user']['name'] == test_user['name']
        assert data['user']['email'] == test_user['email']
        assert data['user']['role'] == test_user['role']