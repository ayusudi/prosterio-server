from flask import Blueprint, request, jsonify, current_app
from app.db import get_connection
import bcrypt
import random
import string
from datetime import datetime, timedelta
from flask_mail import Mail, Message

forgot_password_bp = Blueprint('forgot_password', __name__, url_prefix='/api/forgot-password')

def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))

@forgot_password_bp.route('/request', methods=['POST'])
def request_reset():
    """
    Request password reset
    ---
    tags:
      - Authentication
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              description: User email
              example: user@example.com
    responses:
      200:
        description: OTP sent successfully
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Bad request
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: User not found
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
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT id FROM Users WHERE email = %s AND is_deleted = FALSE", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Generate OTP and set expiry time (2 hours from now)
        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=15)
        
        # Send email with OTP
        try:
            mail = Mail(current_app)
            msg = Message(
                'Password Reset Request - Prosterio',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            
            msg.body = f"""
Hello,

You have requested to reset your password for your Prosterio account.

Your OTP code is: {otp}

This code will expire in 15 minutes. Please do not share this code with anyone.

If you did not request this password reset, please ignore this email.

Best regards,
Prosterio Team
            """
            
            mail.send(msg)
        except Exception as e:
            print(f"Email error details: {str(e)}")  # For debugging
            return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

        # Update user with OTP and expiry time
        cursor.execute("""
            UPDATE Users 
            SET otp_code = %s, expired_otp = %s 
            WHERE email = %s
        """, (otp, expiry_time, email))
        
        conn.commit()

        return jsonify({
            "message": "OTP sent successfully to your email"
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@forgot_password_bp.route('/verify', methods=['POST'])
def verify_otp():
    """
    Verify OTP and reset password
    ---
    tags:
      - Authentication
    security: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              description: User email
            otp:
              type: string
              description: OTP code
            new_password:
              type: string
              description: New password
    responses:
      200:
        description: Password reset successful
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Invalid or expired OTP
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: User not found
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
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')
    new_password = data.get('new_password')

    if not all([email, otp, new_password]):
        return jsonify({"error": "Email, OTP, and new password are required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get user with OTP
        cursor.execute("""
            SELECT id, otp_code, expired_otp 
            FROM Users 
            WHERE email = %s AND is_deleted = FALSE
        """, (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user_id, stored_otp, expiry_time = user

        # Check if OTP matches and is not expired
        if not stored_otp or stored_otp != otp:
            return jsonify({"error": "Invalid OTP"}), 400

        if expiry_time < datetime.now():
            return jsonify({"error": "OTP has expired"}), 400

        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update password and clear OTP
        cursor.execute("""
            UPDATE Users 
            SET password = %s, otp_code = NULL, expired_otp = NULL 
            WHERE id = %s
        """, (hashed_password, user_id))
        
        conn.commit()

        return jsonify({"message": "Password reset successful"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()