import os
import json
import pytest
from app import create_app
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

def test_verify_otp_valid(client, monkeypatch):
    """Test verifying valid OTP"""
    # Buat request dengan OTP valid
    data = {
        'email': os.getenv("TEST_USER_EMAIL"),
        'otp': '123456',
        'new_password': 'NewPassword123'
    }
    
    # Mock database query to return a valid user with matching OTP
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1, '123456', datetime.now() + timedelta(minutes=5))
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the database connection
    monkeypatch.setattr('app.routes.forgot_password.get_connection', lambda: mock_conn)
    
    # Kirim request
    response = client.post('/api/forgot-password/verify', 
                          json=data)
    
    # Periksa response
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'message' in result
    assert 'reset' in result['message'].lower()
    
    
def test_verify_otp_invalid(client, monkeypatch):
    """Test verifying invalid OTP"""
    # Buat request dengan OTP tidak valid
    data = {
        'email': os.getenv("TEST_USER_EMAIL"),
        'otp': '999999',
        'new_password': 'NewPassword123'
    }
    
    # Mock database query to return a user with non-matching OTP
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1, '123456', datetime.now() + timedelta(minutes=5))
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the database connection
    monkeypatch.setattr('app.routes.forgot_password.get_connection', lambda: mock_conn)
    
    # Kirim request
    response = client.post('/api/forgot-password/verify', 
                            json=data)
    
    # Periksa response
    assert response.status_code == 400
    result = json.loads(response.data)
    assert 'error' in result
    assert 'Invalid OTP' in result['error']


def test_forgot_password_request_valid_email(client, monkeypatch):
    """Test forgot password request with valid email"""
    # Mock the Mail class and send method
    mock_mail = MagicMock()
    monkeypatch.setattr('app.routes.forgot_password.Mail', lambda app: mock_mail)
    
    # Mock database query to return a valid user
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)  # User ID
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the database connection
    monkeypatch.setattr('app.routes.forgot_password.get_connection', lambda: mock_conn)
    
    # Buat request dengan email valid
    data = {
        'email': os.getenv("TEST_USER_EMAIL")
    }
    
    # Kirim request
    response = client.post('/api/forgot-password/request', 
                          json=data)
    
    # Periksa response
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'message' in result
    assert 'OTP' in result['message']
    
    # Verify mail.send was called
    assert mock_mail.send.called


def test_forgot_password_request_invalid_email(client, monkeypatch):
    """Test forgot password request with invalid email"""
    # Mock database query to return no user
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock the database connection
    monkeypatch.setattr('app.routes.forgot_password.get_connection', lambda: mock_conn)
    
    # Buat request dengan email tidak valid
    data = {
        'email': 'nonexistent@example.com'
    }
    
    # Kirim request
    response = client.post('/api/forgot-password/request', 
                          json=data)
    
    # Periksa response
    assert response.status_code == 404
    result = json.loads(response.data)
    assert 'error' in result
    assert result['error'] == 'User not found'
