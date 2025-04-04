from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import os
from app.db import get_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

SECRET_KEY = os.getenv("JWT_SECRET")

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: Login
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: user@example.com
            password:
              type: string
              example: mypassword
    responses:
      200:
        description: Login successful
        schema:
          properties:
            access_token:
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
      401:
        description: Invalid credentials
    """
    data = request.get_json()

    email = data.get('email')
    input_password = data.get('password')  # plain text

    if not email or not input_password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name, email, password, role FROM Users WHERE email = %s AND is_deleted = FALSE", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        user_id, name, email, password, role  = user
        print(user_id, name, password)
        hashed_password = bytes(password)
        
        # bcrypt needs the stored password as bytes
        if not bcrypt.checkpw(input_password.encode('utf-8'), hashed_password):
            return jsonify({"error": "Invalid email or password"}), 401

        # JWT Payload
        token = jwt.encode({
            "id": user_id,
            "email": email,
            "role": role
        }, SECRET_KEY, algorithm="HS256")

        return jsonify({
            "access_token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role
            }
        })

    finally:
        cursor.close()
        conn.close()
