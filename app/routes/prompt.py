from flask import Blueprint, request, jsonify

prompt_bp = Blueprint('prompt', __name__, url_prefix='/api')

prompts = []

@prompt_bp.route('/prompt', methods=['POST'])
def handle_prompt():
    data = request.json
    prompts.append(data)
    return jsonify({"message": "Prompt received", "data": data})
