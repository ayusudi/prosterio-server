from flask import Blueprint, request, jsonify, g
from app.db import get_connection
from flasgger import swag_from

employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

@employees_bp.route('', methods=['POST'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Create a new employee with content chunks',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'full_name': {'type': 'string', 'example': 'Jane Doe'},
                    'job_title': {'type': 'string', 'example': 'AI Researcher'},
                    'email': {'type': 'string', 'example': 'jane.doe@prosterio.ai'},
                    'skills': {'type': 'array', 'items': {'type': 'string'}, 'example': ['Python', 'RAG']},
                    'file_url': {'type': 'string', 'example': 'https://files.prosterio.ai/jane_resume.pdf'},
                    'resign_status': {'type': 'boolean', 'example': False},
                    'resign_date': {'type': 'string', 'format': 'date-time', 'example': None},
                    'content_chunks': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'chunk_text': {'type': 'string', 'example': 'Skilled in machine learning'},
                                'type': {'type': 'string', 'example': 'summary'}
                            }
                        }
                    }
                },
                'required': ['full_name', 'job_title', 'email']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Employee and content chunks created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'employee_id': {'type': 'integer'}
                }
            }
        },
        400: {'description': 'Invalid input or database error'}
    }
})
def create_employee():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO employees (
                full_name, job_title, email, skills, file_url, user_id, resign_status, resign_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['full_name'],
            data['job_title'],
            data['email'],
            data.get('skills'),
            data.get('file_url'),
            g.user_id,
            data.get('resign_status', False),
            data.get('resign_date', None)
        ))

        new_employee_id = cursor.fetchone()[0]

        content_chunks = data.get('content_chunks', [])
        for chunk in content_chunks:
            cursor.execute("""
                INSERT INTO content_chunks (
                    chunk_text, type, user_id, employee_id
                ) VALUES (%s, %s, %s, %s)
            """, (
                chunk['chunk_text'],
                chunk['type'],
                g.user_id,
                new_employee_id
            ))

        conn.commit()
        return jsonify({
            "message": "Employee and content chunks created successfully",
            "employee_id": new_employee_id
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


@employees_bp.route('', methods=['GET'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Get all employees',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'List of employees',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'full_name': {'type': 'string'},
                        'job_title': {'type': 'string'},
                        'email': {'type': 'string'},
                        'file_url': {'type': 'string'},
                        'resign_status': {'type': 'boolean'},
                        'resign_date': {'type': 'string', 'format': 'date-time'}
                    }
                }
            }
        }
    }
})
def get_employees():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, full_name, job_title, email, file_url, resign_status, resign_date
            FROM employees
        """)
        rows = cursor.fetchall()
        employees = [
            {
                "id": row[0],
                "full_name": row[1],
                "job_title": row[2],
                "email": row[3],
                "file_url": row[4],
                "resign_status": row[5],
                "resign_date": row[6]
            }
            for row in rows
        ]
        return jsonify(employees)
    finally:
        cursor.close()
        conn.close()


@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Update employee details',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'employee_id', 'in': 'path', 'required': True, 'type': 'integer'},
        {'name': 'body', 'in': 'body', 'required': True,
         'schema': {
             'type': 'object',
             'properties': {
                 'full_name': {'type': 'string'},
                 'job_title': {'type': 'string'},
                 'email': {'type': 'string'},
                 'skills': {'type': 'array', 'items': {'type': 'string'}},
                 'file_url': {'type': 'string'}
             }
         }}
    ],
    'responses': {
        200: {'description': 'Employee updated successfully'},
        404: {'description': 'Employee not found'}
    }
})
def update_employee(employee_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE employees
            SET full_name = %s,
                job_title = %s,
                email = %s,
                skills = %s,
                file_url = %s,
                updated_at = CURRENT_TIMESTAMP()
            WHERE id = %s
        """, (
            data.get('full_name'),
            data.get('job_title'),
            data.get('email'),
            data.get('skills'),
            data.get('file_url'),
            employee_id
        ))

        if cursor.rowcount == 0:
            return jsonify({'error': 'Employee not found'}), 404

        conn.commit()
        return jsonify({'message': 'Employee updated successfully'}), 200
    finally:
        cursor.close()
        conn.close()


@employees_bp.route('/<int:employee_id>/resign', methods=['PATCH'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Resign employee and remove content chunks',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'employee_id', 'in': 'path', 'required': True, 'type': 'integer'}
    ],
    'responses': {
        200: {'description': 'Employee resigned and content chunks removed'},
        404: {'description': 'Employee not found'}
    }
})
def resign_employee(employee_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE employees
            SET resign_status = TRUE,
                resign_date = CURRENT_TIMESTAMP(),
                updated_at = CURRENT_TIMESTAMP()
            WHERE id = %s
        """, (employee_id,))

        if cursor.rowcount == 0:
            return jsonify({'error': 'Employee not found'}), 404

        cursor.execute("DELETE FROM content_chunks WHERE employee_id = %s", (employee_id,))

        conn.commit()
        return jsonify({'message': 'Employee resigned and content chunks removed'}), 200
    finally:
        cursor.close()
        conn.close()
