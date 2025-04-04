from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    return jsonify({"message": "Logged in", "data": data})
