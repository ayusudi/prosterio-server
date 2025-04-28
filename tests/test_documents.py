import json
import os
from unittest.mock import patch, MagicMock

def test_extract_with_gemini_no_files(client):
    response = client.post('/api/documents', data={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == 'No PDF files uploaded'

@patch('app.routes.documents.genai')
@patch('app.routes.documents.PyPDFLoader')
def test_extract_with_gemini_success(mock_loader, mock_genai, client):
    # Mock PDF loader
    mock_page = MagicMock()
    mock_page.page_content = 'Test CV content'
    mock_loader.return_value.load_and_split.return_value = [mock_page]
    
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = '{"full_name": "John Doe", "email": "john@example.com"}'
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Create test PDF file
    test_file = (b'dummy pdf content', 'test.pdf')
    
    response = client.post('/api/documents',
                          data={'documents': test_file},
                          content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1
    assert 'filename' in data[0]
    assert 'data' in data[0]
    assert data[0]['data']['full_name'] == 'John Doe'

@patch('app.routes.documents.genai')
def test_extract_with_gemini_no_api_key(mock_genai, client):
    with patch.dict(os.environ, {'GEMINI_APIKEY': ''}):
        test_file = (b'dummy pdf content', 'test.pdf')
        response = client.post('/api/documents',
                              data={'documents': test_file},
                              content_type='multipart/form-data')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'GEMINI_APIKEY not found'

@patch('app.routes.documents.genai')
@patch('app.routes.documents.PyPDFLoader')
def test_extract_with_gemini_invalid_response(mock_loader, mock_genai, client):
    # Mock PDF loader
    mock_page = MagicMock()
    mock_page.page_content = 'Test CV content'
    mock_loader.return_value.load_and_split.return_value = [mock_page]
    
    # Mock Gemini response with invalid JSON
    mock_response = MagicMock()
    mock_response.text = 'Invalid JSON response'
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    
    test_file = (b'dummy pdf content', 'test.pdf')
    response = client.post('/api/documents',
                          data={'documents': test_file},
                          content_type='multipart/form-data')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1
    assert 'error' in data[0]