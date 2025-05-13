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
    print(data)
    return {'Authorization': f'Bearer {data["access_token"]}'}

def test_get_employees(client, auth_headers):
    """Test getting all employees"""
    response = client.get('/api/employees', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_create_employee(client, auth_headers):
    """Test creating a new employee"""
    # Create a test employee
    import uuid
    unique_email = f"employee_{uuid.uuid4().hex[:8]}@example.com"
    
    employee_data = {
        'employees': [{
            'full_name': 'Test Employee',
            'email': unique_email,
            'job_title': 'Software Engineer',
            'promotion_years': 2,
            'profile': 'Test profile',
            'skills': ['Python', 'Flask', 'SQL'],
            'professional_experiences': [{
                'company': 'Test Company',
                'job_title': 'Junior Developer',
                'date_start': 'Jan 2020',
                'date_end': 'Current',
                'description': 'Worked on various projects'
            }],
            'educations': [{
                'institution': 'Test University',
                'title': 'Computer Science',
                'score': '3.8/4.0',
                'date_start': '2016',
                'date_end': '2020',
                'description': 'Studied computer science'
            }],
            'publications': [],
            'distinctions': [],
            'certifications': ['AWS Certified Developer']
        }]
    }
    
    response = client.post('/api/employees', 
                          headers=auth_headers,
                          json=employee_data)
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'results' in data
    assert len(data['results']) > 0
    assert data['results'][0]['email'] == unique_email
    
    # Store the employee ID for later tests
    employee_id = data['results'][0]['employee_id']
    return employee_id

def test_get_employee_by_id(client, auth_headers):
    """Test getting an employee by ID"""
    # First create an employee
    employee_id = test_create_employee(client, auth_headers)
    
    # Now get the employee
    response = client.get(f'/api/employees/{employee_id}', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == employee_id

def test_update_employee(client, auth_headers):
    """Test updating an employee"""
    # First create an employee
    employee_id = test_create_employee(client, auth_headers)
    
    # Get the current employee data
    get_response = client.get(f'/api/employees/{employee_id}', headers=auth_headers)
    employee_data = json.loads(get_response.data)
    
    # Update some fields
    employee_data['full_name'] = 'Updated Employee Name'
    employee_data['job_title'] = 'Senior Software Engineer'
    
    # Send the update
    update_response = client.put(f'/api/employees/{employee_id}', 
                                headers=auth_headers,
                                json=employee_data)
    
    assert update_response.status_code == 200
    data = json.loads(update_response.data)
    assert 'message' in data
    assert data['employee_id'] == employee_id
    
    # Verify the update
    verify_response = client.get(f'/api/employees/{employee_id}', headers=auth_headers)
    updated_data = json.loads(verify_response.data)
    assert updated_data['full_name'] == 'Updated Employee Name'
    assert updated_data['job_title'] == 'Senior Software Engineer'

def test_delete_employee(client, auth_headers):
    """Test deleting an employee"""
    # First create an employee
    employee_id = test_create_employee(client, auth_headers)
    
    # Now delete the employee
    response = client.delete(f'/api/employees/{employee_id}', headers=auth_headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    
    # Verify the employee is deleted
    verify_response = client.get(f'/api/employees/{employee_id}', headers=auth_headers)
    assert verify_response.status_code == 404