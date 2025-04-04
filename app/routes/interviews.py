from flask import Blueprint, request, jsonify

interviews_bp = Blueprint('interviews', __name__, url_prefix='/api/interviews')
interviews = []

@interviews_bp.route('', methods=['POST'])
def create_interview():
    data = request.json
    interviews.append(data)
    return jsonify({"message": "Interview created", "data": data})

@interviews_bp.route('/<int:int_id>', methods=['PUT'])
def update_interview(int_id):
    if int_id < len(interviews):
        interviews[int_id].update(request.json)
        return jsonify({"message": "Interview updated", "data": interviews[int_id]})
    return jsonify({"error": "Interview not found"}), 404
