import json
import pytest
import io
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

@pytest.fixture
def real_pdf():
    """Use a real PDF file for testing"""
    pdf_path = os.path.join(os.path.dirname(__file__), 'pdf', 'CV-IntanPermataSari-BusinessAnalyst.pdf')
    with open(pdf_path, 'rb') as f:
        return io.BytesIO(f.read())

def test_upload_file(client, auth_headers, real_pdf, monkeypatch):
    """Test uploading a file to Google Drive"""
    # Mock the Google Drive service
    from unittest.mock import MagicMock
    
    # Create mock file response
    mock_file = {
        'id': 'test_file_id',
        'webViewLink': 'https://drive.google.com/file/d/test_file_id/view'
    }
    
    # Mock the files().create().execute() method
    mock_create = MagicMock()
    mock_create.execute.return_value = mock_file
    
    # Mock the files() method
    mock_files = MagicMock()
    mock_files.create.return_value = mock_create
    
    # Mock the permissions().create().execute() method
    mock_perm_create = MagicMock()
    mock_perm_create.execute.return_value = {}
    
    # Mock the permissions() method
    mock_permissions = MagicMock()
    mock_permissions.create.return_value = mock_perm_create
    
    # Mock the drive service
    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value = mock_files
    mock_drive_service.permissions.return_value = mock_permissions
    
    # Mock the get_google_drive_service function
    monkeypatch.setattr('app.routes.gdrive.get_google_drive_service', lambda: mock_drive_service)
    
    # Create the request data with the real PDF
    data = {
        'file': (real_pdf, 'CV-IntanPermataSari-BusinessAnalyst.pdf'),
        'file_name': 'CV-IntanPermataSari-BusinessAnalyst'
    }
    
    response = client.post('/api/gdrive', 
                          headers=auth_headers,
                          data=data,
                          content_type='multipart/form-data')
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'file_id' in result
    assert 'web_view_link' in result
    assert result['file_id'] == 'test_file_id'
    assert result['web_view_link'] == 'https://drive.google.com/file/d/test_file_id/view'