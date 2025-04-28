import json
from unittest.mock import patch

def test_create_employee(client):
    test_data = {
        'full_name': 'John Doe',
        'job_title': 'Software Engineer',
        'email': 'john@example.com',
        'skills': ['Python', 'Flask'],
        'file_url': 'https://example.com/cv.pdf',
        'content_chunks': [
            {'chunk_text': 'Experienced developer', 'type': 'summary'}
        ]
    }
    
    with patch('app.routes.employees.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = [1]  # Return employee_id
        
        response = client.post('/api/employees',
                              json=test_data,
                              headers={'Authorization': 'Bearer test-token'})
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'employee_id' in data
        assert 'message' in data

def test_get_employees(client):
    test_employees = [
        (1, 'John Doe', 'Engineer', 'john@example.com', 'file.pdf', False, None),
        (2, 'Jane Smith', 'Designer', 'jane@example.com', 'file2.pdf', True, '2024-01-01')
    ]
    
    with patch('app.routes.employees.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = test_employees
        
        response = client.get('/api/employees',
                             headers={'Authorization': 'Bearer test-token'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['full_name'] == 'John Doe'
        assert data[1]['full_name'] == 'Jane Smith'

def test_update_employee(client):
    employee_id = 1
    update_data = {
        'full_name': 'John Updated',
        'job_title': 'Senior Engineer',
        'email': 'john.updated@example.com',
        'skills': ['Python', 'Flask', 'AWS']
    }
    
    with patch('app.routes.employees.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.rowcount = 1  # Simulate successful update
        
        response = client.put(f'/api/employees/{employee_id}',
                             json=update_data,
                             headers={'Authorization': 'Bearer test-token'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Employee updated successfully'

def test_update_nonexistent_employee(client):
    employee_id = 999
    update_data = {'full_name': 'John Updated'}
    
    with patch('app.routes.employees.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.rowcount = 0  # Simulate no rows affected
        
        response = client.put(f'/api/employees/{employee_id}',
                             json=update_data,
                             headers={'Authorization': 'Bearer test-token'})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

def test_resign_employee(client):
    employee_id = 1
    
    with patch('app.routes.employees.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.rowcount = 1  # Simulate successful update
        
        response = client.patch(f'/api/employees/{employee_id}/resign',
                               headers={'Authorization': 'Bearer test-token'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Employee resigned and content chunks removed'

def test_resign_nonexistent_employee(client):
    employee_id = 999
    
    with patch('app.routes.employees.get_connection') as mock_conn:
        mock_cursor = mock_conn.return_value.cursor.return_value
        mock_cursor.rowcount = 0  # Simulate no rows affected
        
        response = client.patch(f'/api/employees/{employee_id}/resign',
                               headers={'Authorization': 'Bearer test-token'})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data