from flask import Blueprint, request, jsonify

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
projects = []

@projects_bp.route('', methods=['POST'])
def create_project():
    data = request.json
    projects.append(data)
    return jsonify({"message": "Project created", "data": data})
