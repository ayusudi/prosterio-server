from flask import Blueprint, request, jsonify

rag_bp = Blueprint('rag', __name__, url_prefix='/api')

rag_data = []

@rag_bp.route('/rag', methods=['POST'])
def handle_rag():
    data = request.json
    rag_data.append(data)
    return jsonify({"message": "RAG data processed", "data": data})
