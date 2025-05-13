import json
import pytest
import os
import io
from app import create_app
import os
from pathlib import Path


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

def test_extract_with_gemini(client, auth_headers, real_pdf, monkeypatch):
    """Test document extraction with Gemini"""
    # Mock the Gemini API response
    from unittest.mock import MagicMock
    
    # Create a mock response for genai.GenerativeModel().generate_content()
    mock_response = MagicMock()
    mock_response.text = """
    {
      "full_name": "Intan Permata Sari",
      "email": "intanpermatasari@gmail.com",
      "job_title": "Business Analyst",
      "promotion_years": 2,
      "profile": "Experienced business analyst with a focus on data analysis and project management.",
      "skills": ["Data Analysis", "Project Management", "SQL", "Business Intelligence"],
      "professional_experiences": [
        {
          "company": "Tech Company",
          "job_title": "Business Analyst",
          "date_start": "Jan 2020",
          "date_end": "Current",
          "description": "Analyzing business requirements and translating them into technical specifications"
        }
      ],
      "educations": [
        {
          "institution": "University",
          "title": "Business Administration",
          "score": "3.8/4.0",
          "date_start": "2016",
          "date_end": "2020",
          "description": "Studied business administration with focus on data analytics"
        }
      ],
      "publications": [],
      "distinctions": [],
      "certifications": ["Business Analysis Professional Certification"]
    }
    """
    
    # Mock the GenerativeModel class
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    
    # Mock the genai module
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Apply the mock
    monkeypatch.setattr('google.generativeai', mock_genai)
    
    # Create a test request with the real PDF
    data = {'documents': (real_pdf, 'CV-IntanPermataSari-BusinessAnalyst.pdf')}
    response = client.post('/api/documents', 
                          headers=auth_headers,
                          data=data,
                          content_type='multipart/form-data')
    
    # Check the response
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'data' in result
    assert len(result['data']) > 0
    assert result['data'][0]['filename'] == 'CV-IntanPermataSari-BusinessAnalyst.pdf'
    assert 'data' in result['data'][0]
    assert result['data'][0]['data']['full_name'] == 'Intan Permata Sari'