import json
from unittest.mock import patch
import bcrypt

def test_create_user_success(client, auth_headers):
    test_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass123',
        'role': 'HR'
    }
    print(auth_headers)
    
    with patch('app.routes.users.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = None  # No existing user
        
        response = client.post('/api/users',
                              json=test_data,
                              headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User created successfully'
        assert data['data']['name'] == test_data['name']
        assert data['data']['email'] == test_data['email']
        assert data['data']['role'] == test_data['role']

# def test_create_user_missing_fields(client, auth_headers):
#     test_data = {
#         'name': 'Test User',
#         'email': 'test@example.com'
#         # Missing password and role
#     }
    
#     response = client.post('/api/users',
#                           json=test_data,
#                           headers=auth_headers)
    
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert 'error' in data
#     assert data['error'] == 'Missing required fields'

# def test_create_user_existing_email(client, auth_headers):
#     test_data = {
#         'name': 'Test User',
#         'email': 'existing@example.com',
#         'password': 'testpass123',
#         'role': 'user'
#     }
    
#     with patch('app.routes.users.get_connection') as mock_conn:
#         mock_cursor = mock_conn.return_value.cursor.return_value
#         mock_cursor.fetchone.return_value = [1]  # Existing user found
        
#         response = client.post('/api/users',
#                               json=test_data,
#                               headers=auth_headers)
        
#         assert response.status_code == 409
#         data = json.loads(response.data)
#         assert data['error'] == 'Email already exists'

# def test_create_user_password_hashing_error(client, auth_headers):
#     test_data = {
#         'name': 'Test User',
#         'email': 'test@example.com',
#         'password': 'testpass123',
#         'role': 'user'
#     }
    
#     with patch('bcrypt.hashpw') as mock_hashpw:
#         mock_hashpw.side_effect = Exception('Hashing error')
        
#         response = client.post('/api/users',
#                               json=test_data,
#                               headers=auth_headers)
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Password hashing failed' in data['error']

# def test_create_user_database_error(client, auth_headers):
#     test_data = {
#         'name': 'Test User',
#         'email': 'test@example.com',
#         'password': 'testpass123',
#         'role': 'user'
#     }
    
#     with patch('app.routes.users.get_connection') as mock_conn:
#         mock_cursor = mock_conn.return_value.cursor.return_value
#         mock_cursor.fetchone.side_effect = [None, Exception('Database error')]
#         mock_conn.return_value.rollback = lambda: None
        
#         response = client.post('/api/users',
#                               json=test_data,
#                               headers=auth_headers)
        
#         assert response.status_code == 500
#         data = json.loads(response.data)
#         assert 'error' in data
#         assert 'Database error' in data['error']
#         mock_conn.return_value.rollback.assert_called_once()

# def test_create_user_unauthorized(client):
#     test_data = {
#         'name': 'Test User',
#         'email': 'test@example.com',
#         'password': 'testpass123',
#         'role': 'user'
#     }
    
#     response = client.post('/api/users',
#                           json=test_data,
#                           headers={'Content-Type': 'application/json'})
    
#     assert response.status_code == 401
#     data = json.loads(response.data)
#     assert 'error' in data
#     assert data['error'] == 'Missing or invalid Authorization header'


# def test_get_all_users_success(client, auth_headers):
#     mock_users = [
#         {
#             'id': 1,
#             'name': 'Test User 1',
#             'email': 'test1@example.com',
#             'role': 'SUPERUSER'
#         },
#         {
#             'id': 2,
#             'name': 'Test User 2',
#             'email': 'test2@example.com',
#             'role': 'USER'
#         }
#     ]
    
#     with patch('app.routes.users.get_connection') as mock_conn:
#         mock_cursor = mock_conn.return_value.cursor.return_value
#         mock_cursor.fetchall.return_value = mock_users
        
#         response = client.get('/api/users', headers=auth_headers)
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'data' in data
#         assert len(data['data']) == 2
#         assert data['data'][0]['name'] == mock_users[0]['name']
#         assert data['data'][1]['email'] == mock_users[1]['email']

# def test_get_user_by_id_success(client, auth_headers):
#     mock_user = {
#         'id': 1,
#         'name': 'Test User',
#         'email': 'test@example.com',
#         'role': 'SUPERUSER'
#     }
    
#     with patch('app.routes.users.get_connection') as mock_conn:
#         mock_cursor = mock_conn.return_value.cursor.return_value
#         mock_cursor.fetchone.return_value = mock_user
        
#         response = client.get('/api/users/1', headers=auth_headers)
        
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert 'data' in data
#         assert data['data']['id'] == mock_user['id']
#         assert data['data']['name'] == mock_user['name']
#         assert data['data']['email'] == mock_user['email']
#         assert data['data']['role'] == mock_user['role']