from flask import Blueprint, request, jsonify

clients_bp = Blueprint('clients', __name__, url_prefix='/api/clients')
clients = []

@clients_bp.route('', methods=['POST'])
def create_client():
    data = request.json
    clients.append(data)
    return jsonify({"message": "Client created", "data": data})
