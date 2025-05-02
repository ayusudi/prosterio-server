from flask import Blueprint, request, jsonify, g
from app.db import get_connection
from datetime import datetime
import json

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
        cur.execute("SELECT * FROM PROSTERIO.PUBLIC.CHATS WHERE IS_DELETED = FALSE AND USER_ID = %s ORDER BY CREATED_AT DESC", (g.user_id,))
        chats = cur.fetchall()
        
        result = []
        for chat in chats:
            # Convert timestamps to Jakarta timezone
            result.append({
                "id": chat[0],
                "title": chat[1],
                "chats": chat[2],
                "user_id": chat[3],
                "created_at": chat[4],
                "updated_at": chat[5],
            })
        
        return jsonify({"chats": result})
    except Exception as e:
        print(e)
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
            properties:
              title:
                type: string
                description: Title of the chat
              chats:
                type: object
                description: Chat content
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
      400:
        description: Missing required fields
      500:
        description: Internal server error
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        data = request.json
        required_fields = ['title', 'chats']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
       
        # Convert chats to a properly formatted JSON string
        chats_json = json.dumps(data['chats'], ensure_ascii=False)
        
        sql = f"""
        INSERT INTO PROSTERIO.PUBLIC.CHATS (TITLE, CHATS, USER_ID)
        SELECT %s, PARSE_JSON(%s), %s
        """
        cur.execute(sql, (data['title'], chats_json, g.user_id))
        conn.commit()
        return jsonify({"message": "Chat created"})
    except Exception as e:
        print(e)
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
        
        cur.execute("SELECT * FROM PROSTERIO.PUBLIC.CHATS WHERE ID = %s AND IS_DELETED = FALSE AND USER_ID = %s", (chat_id, g.user_id))
        chat = cur.fetchone()
        
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
            
        result = {
            "id": chat[0],
            "title": chat[1],
            "chats": chat[2],
            "user_id": chat[3],
            "created_at": chat[4],
            "updated_at": chat[5],
        }
        
        return jsonify({"chat": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@chats_bp.route('/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """
    Delete a chat by ID (soft delete)
    ---
    tags:
      - Chats
    parameters:
      - name: chat_id
        in: path
        required: true
        schema:
          type: integer
        description: ID of the chat to delete
    responses:
      200:
        description: Chat deleted successfully
      404:
        description: Chat not found
      500:
        description: Internal server error
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # First check if the chat exists and belongs to the user
        cur.execute("SELECT ID FROM PROSTERIO.PUBLIC.CHATS WHERE ID = %s AND USER_ID = %s AND IS_DELETED = FALSE", (chat_id, g.user_id))
        chat = cur.fetchone()
        
        if not chat:
            return jsonify({"error": "Chat not found"}), 404
            
        cur.execute("""
            UPDATE PROSTERIO.PUBLIC.CHATS 
            SET IS_DELETED = TRUE, 
                DELETED_AT = CURRENT_TIMESTAMP()
            WHERE ID = %s AND USER_ID = %s
        """, (chat_id, g.user_id))
        
        conn.commit()
        return jsonify({"message": "Chat deleted"}), 200
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
