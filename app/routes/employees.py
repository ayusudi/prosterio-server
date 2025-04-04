from flask import Blueprint, request, jsonify
from app.db import get_connection

employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

@employees_bp.route('', methods=['POST'])
def create_employee():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO employees (name) VALUES (%s, %s)",
            (data['name'])
        )
        return jsonify({"message": "Employee added", "data": data})
    finally:
        cursor.close()
        conn.close()

@employees_bp.route('', methods=['GET'])
def get_employees():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM employees")
        rows = cursor.fetchall()
        employees = [{"id": r[0], "name": r[1]} for r in rows]
        return jsonify(employees)
    finally:
        cursor.close()
        conn.close()
