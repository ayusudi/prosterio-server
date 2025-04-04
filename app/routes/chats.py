from flask import Blueprint, request, jsonify

chats_bp = Blueprint('chats', __name__, url_prefix='/api/chats')
chats = []

@chats_bp.route('', methods=['GET'])
def get_chats():
    return jsonify({"chats": chats})

@chats_bp.route('', methods=['POST'])
def create_chat():
    data = request.json
    chats.append(data)
    return jsonify({"message": "Chat created", "data": data})

@chats_bp.route('/<int:chat_id>', methods=['GET'])
def get_chat_by_id(chat_id):
    if chat_id < len(chats):
        return jsonify({"chat": chats[chat_id]})
    return jsonify({"error": "Chat not found"}), 404
