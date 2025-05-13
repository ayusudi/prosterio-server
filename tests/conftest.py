import pytest
from app import create_app
import json
import bcrypt
import jwt
import os
import tempfile

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })
    
    # Create the database and load test data
    with app.app_context():
        # Initialize database if needed
        pass
    
    yield app
    
    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
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