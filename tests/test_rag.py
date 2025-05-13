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

def test_handle_rag(client, auth_headers, monkeypatch):
    """Test handling a RAG query"""
    # Mock the Snowflake cursor
    from unittest.mock import MagicMock
    
    # Create mock cursor and connection
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [
        # First call - context
        ["Sample context about employees and their skills"],
        # Second call - response
        ["This is a generated response based on the context"]
    ]
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the get_connection function
    monkeypatch.setattr('app.routes.rag.get_connection', lambda: mock_conn)
    
    # Mock the evaluation functions
    monkeypatch.setattr('app.routes.rag.custom_groundedness', lambda *args: 0.85)
    monkeypatch.setattr('app.routes.rag.custom_relevance', lambda *args: 0.90)
    monkeypatch.setattr('app.routes.rag.cortex_evaluator', lambda *args: {"coherence": 0.88})
    
    # Create a test RAG query
    rag_data = {
        'prompt': 'Who are the best backend developers in our company?'
    }
    
    response = client.post('/api/rag', 
                          headers=auth_headers,
                          json=rag_data)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'answer' in data
    assert 'evaluation' in data
    assert data['answer'] == "This is a generated response based on the context"