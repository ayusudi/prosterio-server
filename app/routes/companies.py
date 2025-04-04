from flask import Blueprint, request, jsonify

companies_bp = Blueprint('companies', __name__, url_prefix='/api/companies')
companies = []

@companies_bp.route('', methods=['POST'])
def create_company():
    data = request.json
    companies.append(data)
    return jsonify({"message": "Company created", "data": data})
