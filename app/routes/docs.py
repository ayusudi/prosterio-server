from flask import Blueprint, request, jsonify

docs_bp = Blueprint('docs', __name__, url_prefix='/api/docs')
docs = []

@docs_bp.route('', methods=['POST'])
def upload_docs():
    data = request.json
    docs.append(data)
    return jsonify({"message": "Document uploaded", "data": data})
