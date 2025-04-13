from flask import Blueprint, request, jsonify, g
from app.db import get_connection
from flasgger import swag_from

clients_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@clients_bp.route('', methods=['POST'])
@swag_from({
    'tags': ['Clients'],
    'summary': 'Create a new client',
    'security': [{'Bearer': []}],  # 👈 this shows the Authorize button
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'company_name': {'type': 'string'}
                },
                'required': ['company_name']
            }
        }
    ],
    'responses': {
        201: {'description': 'Client created successfully'},
        400: {'description': 'Missing company_name'}
    }
})
def create_client():
    data = request.get_json()
    company_name = data.get('company_name')

    if not company_name:
        return jsonify({'error': 'company_name is required'}), 400

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Clients (company_name, user_id)
            VALUES (%s, %s)
        """, (company_name, g.user_id))
        conn.commit()
        return jsonify({'message': 'Client created successfully'}), 201
    finally:
        conn.close()


@clients_bp.route('', methods=['GET'])
@swag_from({
    'tags': ['Clients'],
    'summary': 'Get all clients for authenticated user',
    'security': [{'Bearer': []}],  # 👈 this shows the Authorize button
    'responses': {
        200: {
            'description': 'List of clients',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'company_name': {'type': 'string'},
                        'created_at': {'type': 'string'},
                        'updated_at': {'type': 'string'}
                    }
                }
            }
        }
    }
})
def get_clients():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, company_name, created_at, updated_at
            FROM Clients
        """)
        rows = cur.fetchall()
        clients = [{
            'id': row[0],
            'company_name': row[1],
            'created_at': str(row[2]),
            'updated_at': str(row[3])
        } for row in rows]
        return jsonify(clients)
    finally:
        conn.close()


@clients_bp.route('/<int:client_id>', methods=['PATCH'])
@swag_from({
    'tags': ['Clients'],
    'summary': 'Update a client',
    'security': [{'Bearer': []}],  # 👈 this shows the Authorize button
    'parameters': [
        {
            'name': 'client_id',
            'in': 'path',
            'type': 'integer',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'company_name': {'type': 'string'}
                },
                'required': ['company_name']
            }
        }
    ],
    'responses': {
        200: {'description': 'Client updated'},
        404: {'description': 'Not found or unauthorized'}
    }
})
def update_client(client_id):
    data = request.get_json()
    company_name = data.get('company_name')

    if not company_name:
        return jsonify({'error': 'company_name is required'}), 400

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE Clients
            SET company_name = %s, updated_at = CURRENT_TIMESTAMP()
            WHERE id = %s AND user_id = %s
        """, (company_name, client_id, g.user_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Client not found or unauthorized'}), 404

        conn.commit()
        return jsonify({'message': 'Client updated successfully'})
    finally:
        conn.close()


@clients_bp.route('/<int:client_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Clients'],
    'summary': 'Delete a client',
     'security': [{'Bearer': []}],  # 👈 this shows the Authorize button
    'parameters': [
        {
            'name': 'client_id',
            'in': 'path',
            'type': 'integer',
            'required': True
        }
    ],
    'responses': {
        200: {'description': 'Client deleted'},
        404: {'description': 'Not found or unauthorized'}
    }
})
def delete_client(client_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM Clients
            WHERE id = %s AND user_id = %s
        """, (client_id, g.user_id))

        if cur.rowcount == 0:
            return jsonify({'error': 'Client not found or unauthorized'}), 404

        conn.commit()
        return jsonify({'message': 'Client deleted successfully'})
    finally:
        conn.close()
