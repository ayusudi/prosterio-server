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

def test_handle_prompt(client, auth_headers, monkeypatch):
    """Test handling a prompt"""
    # Mock the Groq client response
    from unittest.mock import MagicMock
    
    # Create a mock response
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a test response from the AI assistant."
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    # Mock the Groq client
    mock_chat_completions = MagicMock()
    mock_chat_completions.create.return_value = mock_response
    
    mock_groq_client = MagicMock()
    mock_groq_client.chat.completions = mock_chat_completions
    
    # Apply the mock
    monkeypatch.setattr('groq.Groq', lambda **kwargs: mock_groq_client)
    
    # Mock the log_to_snowflake function
    monkeypatch.setattr('app.routes.prompt.log_to_snowflake', lambda **kwargs: True)
    
    # Create a test prompt
    prompt_data = {
        'chats': [
            {'role': 'user', 'content': 'What skills should I look for in a backend developer?'}
        ],
        'max_token': 900
    }
    
    response = client.post('/api/prompt', 
                          headers=auth_headers,
                          json=prompt_data)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data