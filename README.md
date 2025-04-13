# Prosterio Server

A Flask-based backend API server for the Prosterio application with JWT authentication and Swagger documentation.

## Features

- RESTful API endpoints
- JWT Authentication
- Swagger API documentation
- PostgreSQL database integration
- Role-based access control

## Tech Stack

- **Framework**: Flask
- **Documentation**: Flasgger/Swagger
- **Authentication**: JWT
- **Database**: PostgreSQL
- **Password Hashing**: bcrypt

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd server-prosterio
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create file .env like this format:
   ```bash
    SNOWFLAKE_USER=
    SNOWFLAKE_PASSWORD=
    SNOWFLAKE_ACCOUNT=
    SNOWFLAKE_WAREHOUSE=
    SNOWFLAKE_DATABASE=
    SNOWFLAKE_SCHEMA=
    JWT_SECRET=
    MISTRAL_APIKEY=
    OPENAI_API_KEY=
    GEMINI_APIKEY=
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## API Documentation

The API documentation is available at `/apidocs` once the application is running.

# Authentication

The API uses JWT (JSON Web Token) for authentication. To access protected endpoints:

1. Obtain a token by sending a POST request to /api/login with valid credentials
2. Include the token in the Authorization header of subsequent requests:

```bash
Authorization: Bearer <your_token>
```
