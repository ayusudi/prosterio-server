import pytest
from app import create_app
import json
import bcrypt
import jwt
import os
import time

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "JWT_SECRET": os.getenv('JWT_SECRET', 'test-secret-key'),
    })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user():
    password = 'testpass123'
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return {
        'name': 'Test Superuser',
        'email': 'test@example.com',
        'password': password,
        'hashed_password': hashed_password,
        'role': 'SUPERUSER'
    }

@pytest.fixture
def auth_headers(client, test_user, app):
    # Mock login response with a test token
    test_token = jwt.encode(
        {
            "id": 1,
            "email": test_user['email'],
            "role": test_user['role'],
            "exp": int(time.time()) + 3600  # Token expires in 1 hour
        },
        app.config['JWT_SECRET'],
        algorithm="HS256"
    )
    return {'Authorization': f'Bearer {test_token}', 'Content-Type': 'application/json'}