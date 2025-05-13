from flask import Flask, redirect
from flasgger import Swagger
from app.routes import register_routes
from app.middleware.auth import init_auth_middleware
from flask_cors import CORS
from flask_mail import Mail
import os

def create_app(test_config=None):
    app = Flask(__name__)

    # Apply test configuration if provided
    if test_config:
        app.config.update(test_config)

    # Configure CORS with specific origins and options
    CORS(app, resources={
        r"/*": {
            "origins": [
                "https://prosterio.vercel.app",
                "http://localhost:3000",
                "http://localhost:5173",
                "https://prosterio.onrender.com"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
            "supports_credentials": True,
            "expose_headers": ["Content-Range", "X-Content-Range"]
        }
    })

    # Configure static file serving for public folder
    app.static_folder = os.path.join(app.root_path, 'public')
    app.static_url_path = '/static'

    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_OTP')
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PS_OTP')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_OTP')

    # Initialize Flask-Mail
    mail = Mail(app)

    swagger_template = {
        "swagger": "2.0",
        "title": "Prosterio API Documentation",
        "info": {
            "title": "Prosterio API Documentation",
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
            "name": "Analytics",
            "description": "Endpoints for analytics dashboard"
        },
        {
            "name": "Chats",
            "description": "Endpoints for managing chat history"
        },
        {
            "name": "Prompt",
            "description": "Endpoints for chat prompts"
        },
        {
            "name": "RAG",
            "description": "Endpoints for feature RAG"
        },
        {
            "name": "Gdrive",
            "description": "Endpoints for upload file to Google Drive"
        }
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
                "title": "Prosterio API Documentation"
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs",
        "title": "Prosterio API Documentation",
        "swagger_ui_bundle_js": '//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js',
        "swagger_ui_standalone_preset_js": '//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js',
        "swagger_ui_css": '//unpkg.com/swagger-ui-dist@3/swagger-ui.css',
        "swagger_ui_config": {
            "docExpansion": "none",
            "filter": True,
            "displayRequestDuration": True,
            "layout": "BaseLayout",
            "deepLinking": True,
            "showExtensions": True,
            "showCommonExtensions": True
        },
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
