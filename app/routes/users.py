from flask import Blueprint, request, jsonify, g
from app.db import get_connection
import bcrypt
from app.middleware.auth import init_auth_middleware

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
          type: object
          properties:
            name:
              type: string
            email:
              type: string
            password:
              type: string
    responses:
      201:
        description: User created successfully
        schema:
          type: object
          properties:
            message:
              type: string
            data:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                email:
                  type: string
                role:
                  type: string
      400:
        description: Bad request
        schema:
          type: object
          properties:
            error:
              type: string
      409:
        description: Email already exists
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = "HR"

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
            RETURNING id
        """, (name, email, hashed_password, role))
        
        user_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "message": "User created successfully",
            "data": {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role
            }
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@users_bp.route('', methods=['GET'])
def get_users():
    """
    Get list of users
    ---
    tags:
      - Users
    responses:
      200:
        description: List of users retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
                  role:
                    type: string
                  created_at:
                    type: string
                    format: date-time
                  updated_at:
                    type: string
                    format: date-time
      500:
        description: Database error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, email, role, created_at, updated_at 
            FROM Users 
            WHERE is_deleted = FALSE
            ORDER BY created_at DESC
        """)
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
                "updated_at": row[5].isoformat() if row[5] else None
            })

        return jsonify({
            "message": "Users retrieved successfully",
            "data": users
        }), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@users_bp.route('/myself', methods=['GET'])
def get_myself():
    """
    Get current user information
    ---
    tags:
      - Users
    responses:
      200:
        description: User information retrieved successfully
        schema:
          type: object
          properties:
            message:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                email:
                  type: string
                role:
                  type: string
                
      404:
        description: User not found
      500:
        description: Database error
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, name, email, role, created_at, updated_at 
            FROM Users 
            WHERE id = %s AND is_deleted = FALSE
        """, (g.user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "message": "User information retrieved successfully",
            "user": {
                "id": user[0],
                "name": user[1],
                "email": user[2],
                "role": user[3]
            }
        }), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()