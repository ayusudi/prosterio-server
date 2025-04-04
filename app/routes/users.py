from flask import Blueprint, request, jsonify
from app.db import get_connection
import bcrypt
from flask import Blueprint, request, jsonify

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('', methods=['POST'])
def create_user():
    """
    Create user
    ---
    tags:
      - Users
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          properties:
            name:
              type: string
            email:
              type: string
            password:
              type: string
            role:
              type: string
    responses:
      201:
        description: User created successfully
    """
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")

    if not all([name, email, password, role]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # returns bytes
    except Exception as e:
        return jsonify({"error": f"Password hashing failed: {str(e)}"}), 500

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check for existing email
        cursor.execute("SELECT 1 FROM Users WHERE email = %s AND is_deleted = FALSE", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already exists"}), 409

        # Insert new user
        cursor.execute("""
            INSERT INTO Users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed_password, role))

        return jsonify({
            "message": "User created successfully",
            "data": {
                "name": name,
                "email": email,
                "role": role
            }
        }), 201
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
