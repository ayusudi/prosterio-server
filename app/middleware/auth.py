from flask import request, jsonify, g, abort
import jwt
import os

def init_auth_middleware(app):
    @app.before_request
    def check_auth():
        # Skip these routes
        exempt_paths = (
            "/apidocs",
            "/swagger.json",
            "/flasgger_static",
            "/static",
            "/api/login",
            "/api/forgot-password",
            "/public/pdfs",
            "/pdfs",
        )
        
        if any(request.path.startswith(path) for path in exempt_paths) or request.path == "/":
            return

        if request.method == 'OPTIONS':
            return
        
        # Get the Authorization header
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        try:
            # Extract the token string
            token_value = token.split("Bearer ")[1]

            # Decode it using your secret key
            decoded = jwt.decode(
                token_value,
                os.getenv('JWT_SECRET'),
                algorithms=["HS256"]
            )
            
            # Attach token payload to g
            g.user_id = decoded.get("id")
            g.user_email = decoded.get("email")
            g.user_role = decoded.get("role")

            if not g.user_id:
                return jsonify({'error': 'Invalid token payload'}), 403

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': f'Token error: {str(e)}'}), 401
