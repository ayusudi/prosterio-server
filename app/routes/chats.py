from flask import Blueprint, request, jsonify
from app.db import get_connection
from datetime import datetime

chats_bp = Blueprint('chats', __name__, url_prefix='/api/chats')

@chats_bp.route('', methods=['GET'])
def get_chats():
    """
    Get all chats
    ---
    tags:
      - Chats
    responses:
      200:
        description: List of all chats
        content:
          application/json:
            schema:
              type: object
              properties:
                chats:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      title:
                        type: string
                      chats:
                        type: object
                      created_at:
                        type: string
                        format: date-time
                      updated_at:
                        type: string
                        format: date-time
                      user_id:
                        type: integer
      500:
        description: Internal server error
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM PROSTERIO.PUBLIC.CHATS ORDER BY CREATED_AT DESC")
        chats = cur.fetchall()
        
        result = []
        for chat in chats:
            result.append({
                "id": chat[0],
                "title": chat[1],
                "chats": chat[2],
                "created_at": chat[3].isoformat(),
                "updated_at": chat[4].isoformat(),
                "user_id": chat[5]
            })
        
        return jsonify({"chats": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@chats_bp.route('', methods=['POST'])
def create_chat():
    """
    Create a new chat
    ---
    tags:
      - Chats
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - title
              - chats
              - user_id
            properties:
              title:
                type: string
                description: Title of the chat
              chats:
                type: object
                description: Chat content
              user_id:
                type: integer
                description: ID of the user who created the chat
    responses:
      200:
        description: Chat created successfully
        content:
          application/json:
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
                    title:
                      type: string
                    chats:
                      type: object
                    created_at:
                      type: string
                      format: date-time
                    updated_at:
                      type: string
                      format: date-time
                    user_id:
                      type: integer
      400:
        description: Missing required fields
      500:
        description: Internal server error
    """
    try:
        data = request.json
        required_fields = ['title', 'chats', 'user_id']
        
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_connection()
        cur = conn.cursor()
        
        sql = """
        INSERT INTO PROSTERIO.PUBLIC.CHATS (TITLE, CHATS, USER_ID)
        VALUES (%s, %s, %s)
        RETURNING ID, TITLE, CHATS, CREATED_AT, UPDATED_AT, USER_ID
        """
        
        cur.execute(sql, (data['title'], data['chats'], data['user_id']))
        new_chat = cur.fetchone()
        conn.commit()
        
        result = {
            "id": new_chat[0],
            "title": new_chat[1],
            "chats": new_chat[2],
            "created_at": new_chat[3].isoformat(),
            "updated_at": new_chat[4].isoformat(),
            "user_id": new_chat[5]
        }
        
        return jsonify({"message": "Chat created", "data": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@chats_bp.route('/<int:chat_id>', methods=['GET'])
def get_chat_by_id(chat_id):
    """
    Get a chat by ID
    ---
    tags:
      - Chats
    parameters:
      - name: chat_id
        in: path
        required: true
        schema:
          type: integer
        description: ID of the chat to retrieve
    responses:
      200:
        description: Chat details
        content:
          application/json:
            schema:
              type: object
              properties:
                chat:
                  type: object
                  properties:
                    id:
                      type: integer
                    title:
                      type: string
                    chats:
                      type: object
                    created_at:
                      type: string
                      format: date-time
                    updated_at:
                      type: string
                      format: date-time
                    user_id:
                      type: integer
      404:
        description: Chat not found
      500:
        description: Internal server error
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM PROSTERIO.PUBLIC.CHATS WHERE ID = %s", (chat_id,))
        chat = cur.fetchone()
        
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
            
        result = {
            "id": chat[0],
            "title": chat[1],
            "chats": chat[2],
            "created_at": chat[3].isoformat(),
            "updated_at": chat[4].isoformat(),
            "user_id": chat[5]
        }
        
        return jsonify({"chat": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
