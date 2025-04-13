from flask import Flask, redirect
from flasgger import Swagger
from app.routes import register_routes
from app.middleware.auth import init_auth_middleware

def create_app():
    app = Flask(__name__)

    # Make sure your app has CORS enabled if needed
    # from flask_cors import CORS
    # CORS(app)

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Prosterio API",
            "description": "API documentation with JWT bearer token support",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT token. Example: Bearer {token}"
            }
        },
        "security": [{"Bearer": []}],
        "tags": [
        {
            "name": "Authentication",
            "description": "Endpoints for logging in and managing access"
        },
        {
            "name": "Users",
            "description": "Endpoints for user management"
        },
        {
            "name": "Employees",
            "description": "Endpoints for managing employees"
        },
        {
            "name": "Documents",
            "description": "Endpoints for handling documents"
        },
        {
            "name": "Clients",
            "description": "Endpoints for managing clients"
        },
       
    ]
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/swagger.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs",
        "tags": [
        {
            "name": "Authentication",
            "description": "Endpoints for logging in and managing access"
        },
        {
            "name": "Users",
            "description": "Endpoints for user management"
        },
        {
            "name": "Clients",
            "description": "Endpoints for managing clients"
        },
        {
            "name": "Documents",
            "description": "Endpoints for handling documents"
        }
    ]
    }

    # Initialize Swagger before registering routes
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    
    # Register routes before middleware to ensure they're documented
    register_routes(app)
    
    # Initialize auth middleware after routes are registered
    init_auth_middleware(app)
    
    @app.route('/')
    def index():
        return redirect('/apidocs')
    
    @app.route('/apidocs/')
    def redirect_apidocs_trailing_slash():
        return redirect('/apidocs')

    return app
