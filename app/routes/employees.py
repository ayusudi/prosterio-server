# --- Imports ---
from flask import Blueprint, request, jsonify, g
# Replace psycopg2 with snowflake connector
import snowflake.connector
# Keep json for handling VARIANT data before insertion
import json
# Replace get_connection with your Snowflake connection logic
from app.db import get_connection
from flasgger import swag_from
import json # Import json for handling VARIANT types

from app.helpers.chunking import compile_to_chunk

employees_bp = Blueprint('employees', __name__, url_prefix='/api/employees')

# --- Swag definition remains the same ---
@employees_bp.route('', methods=['POST'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Bulk create or update employees',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'employees': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer', 'description': 'Required for updates'},
                                'full_name': {'type': 'string'},
                                'email': {'type': 'string'},
                                'job_title': {'type': 'string'},
                                'promotion_years': {'type': 'integer'},
                                'profile': {'type': 'string'},
                                'skills': {'type': 'array', 'items': {'type': 'string'}},
                                'professional_experiences': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'company': {'type': 'string'},
                                            'job_title': {'type': 'string'},
                                            'date_start': {'type': 'string', 'description': 'MMM YYYY format'},
                                            'date_end': {'type': 'string', 'description': 'MMM YYYY or Current'},
                                            'description': {'type': 'string'} # Should likely be array of strings based on chunking logic? Adjust if needed.
                                        }
                                    }
                                },
                                'educations': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'institution': {'type': 'string'},
                                            'title': {'type': 'string'},
                                            'score': {'type': 'string', 'description': 'score/max_score format'},
                                            'date_start': {'type': 'string', 'description': 'YYYY format'},
                                            'date_end': {'type': 'string', 'description': 'YYYY or Current'},
                                            'description': {'type': 'string'}
                                        }
                                    }
                                },
                                'publications': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'name': {'type': 'string'},
                                            'description': {'type': 'string'},
                                            'link': {'type': 'string'}
                                        }
                                    }
                                },
                                'distinctions': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'name': {'type': 'string'},
                                            'description': {'type': 'string'}
                                        }
                                    }
                                },
                                'certifications': {'type': 'array', 'items': {'type': 'string'}},
                                'file_data': {'type': 'string', 'format': 'binary'}, # Note: Sending large binary data in JSON is inefficient. Consider multipart/form-data or separate upload endpoint.
                                'file_url': {'type': 'string'}
                            },
                            'required': ['full_name', 'email', 'job_title']
                        }
                    }
                },
                'required': ['employees']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Employees created/updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'email': {'type': 'string'},
                                'employee_id': {'type': 'integer'},
                                'status': {'type': 'string'},
                                'error': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        400: {'description': 'Invalid input or database error'}
    }
})
def create_employee():
    try: 
        print("HEI")
        data = request.get_json()
        if not data.get('employees'):
            return jsonify({"error": "No employees data provided"}), 400

        employees_to_process = []
        validation_results = {} # Track validation failures

        for i, employee in enumerate(data['employees']):
            email_key = employee.get('email', f'unknown_{i}')
            if not employee.get('email') or not employee.get('full_name') or not employee.get('job_title'):
                validation_results[email_key] = {"status": "failed", "error": "Missing required fields (email, full_name, job_title)"}
                continue

            # Prepare data: Convert Python dicts/lists directly for VARIANT
            # Snowflake connector handles Python dicts/lists for VARIANT insertion
            processed_employee = employee.copy() # Avoid modifying original dict directly
            for field in ['skills', 'professional_experiences', 'educations', 'publications', 'distinctions', 'certifications']:
                # Keep as Python objects if not None, otherwise set to None
                processed_employee[field] = employee.get(field)

            # Add user_id from global context
            processed_employee['user_id'] = g.user_id
            employees_to_process.append(processed_employee)

        # Filter out employees that failed validation
        valid_employees = [emp for emp in employees_to_process if emp.get('email') not in validation_results]

        if not valid_employees:
            final_results = [{"email": k, **v} for k, v in validation_results.items()]
            return jsonify({"message": "No valid employees to process", "results": final_results}), 400


        conn = None # Initialize conn
        cursor = None # Initialize cursor
        results_map = validation_results.copy() # Start with validation failures

        try:
            conn = get_connection() # Use your Snowflake connection function
            cursor = conn.cursor()

            # --- Use MERGE for Bulk Insert/Update ---
            # Prepare data for MERGE source (list of tuples)
            # Order must match the order in the USING clause's VALUES alias
            merge_data = [
                (
                    emp.get('id'), # Use None for inserts
                    emp['full_name'],
                    emp['email'],
                    emp['job_title'],
                    emp.get('promotion_years'),
                    emp.get('profile'),
                    emp.get('skills'), # Pass Python list directly
                    emp.get('professional_experiences'), # Pass Python list of dicts directly
                    emp.get('educations'),
                    emp.get('publications'),
                    emp.get('distinctions'),
                    emp.get('certifications'),
                    emp.get('file_data'), # Ensure this is bytes if BINARY type
                    emp.get('file_url'),
                    emp['user_id']
                ) for emp in valid_employees
            ]

            # Construct the MERGE statement
            # Note: Snowflake uses %s placeholders
            merge_sql = """
                MERGE INTO employees AS target
                USING (
                    SELECT
                        v.value[0]::INTEGER as id,
                        v.value[1]::VARCHAR as full_name,
                        v.value[2]::VARCHAR as email,
                        v.value[3]::VARCHAR as job_title,
                        v.value[4]::INTEGER as promotion_years,
                        v.value[5]::VARCHAR as profile,
                        PARSE_JSON(v.value[6]::VARCHAR) as skills, -- Parse JSON string if needed, or handle directly if connector supports dicts
                        PARSE_JSON(v.value[7]::VARCHAR) as professional_experiences,
                        PARSE_JSON(v.value[8]::VARCHAR) as educations,
                        PARSE_JSON(v.value[9]::VARCHAR) as publications,
                        PARSE_JSON(v.value[10]::VARCHAR) as distinctions,
                        PARSE_JSON(v.value[11]::VARCHAR) as certifications,
                        BASE64_DECODE_BINARY(v.value[12]::VARCHAR) as file_data,
                        v.value[13]::VARCHAR as file_url,
                        v.value[14]::INTEGER as user_id
                    FROM TABLE(FLATTEN(input => PARSE_JSON(%s))) v -- Pass data as JSON string
                ) AS source
                ON target.id = source.id OR target.email = source.email -- Match on ID for updates, or email if ID is null/not provided
                WHEN MATCHED AND source.id IS NOT NULL THEN -- Update existing based on ID
                    UPDATE SET
                        target.full_name = source.full_name,
                        target.email = source.email,
                        target.job_title = source.job_title,
                        target.promotion_years = source.promotion_years,
                        target.profile = source.profile,
                        target.skills = source.skills,
                        target.professional_experiences = source.professional_experiences,
                        target.educations = source.educations,
                        target.publications = source.publications,
                        target.distinctions = source.distinctions,
                        target.certifications = source.certifications,
                        target.file_data = source.file_data,
                        target.file_url = source.file_url,
                        target.user_id = source.user_id,
                        target.updated_at = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN -- Insert new
                    INSERT (
                        full_name, email, job_title, promotion_years, profile,
                        skills, professional_experiences, educations,
                        publications, distinctions, certifications,
                        file_data, file_url, user_id
                    ) VALUES (
                        source.full_name, source.email, source.job_title, source.promotion_years, source.profile,
                        source.skills, source.professional_experiences, source.educations,
                        source.publications, source.distinctions, source.certifications,
                        source.file_data, source.file_url, source.user_id
                    )
            """

            # Convert the list of tuples/dicts to a JSON string to pass to the query
            # Note: Snowflake connector might have more direct ways for VARIANT, check its docs
            json_data_string = json.dumps(merge_data, default=str) # Use default=str for potential date/binary types

            # Execute the MERGE statement
            cursor.execute(merge_sql, (json_data_string,))
            
            # Fetch the affected rows
            fetch_affected_rows_sql = """
                SELECT id, email
                FROM employees
                WHERE email IN (
                    {}
                );
            """.format(','.join(["'" + emp['email'] + "'" for emp in valid_employees]))
            cursor.execute(fetch_affected_rows_sql)
            merge_results = cursor.fetchall()
            
            # Process the results
            affected_employee_ids = []
            for employee_id, email in merge_results:
                action = "inserted" if email not in results_map else "updated"
                status = f"success ({action})"
                results_map[email] = {"employee_id": employee_id, "status": status}
                affected_employee_ids.append(str(employee_id))
                
            # Bulk delete content chunks for affected employees
            if affected_employee_ids:
                delete_content_chunks_sql = """
                    DELETE FROM Content_Chunks
                    WHERE employee_id IN ({})
                """.format(','.join(affected_employee_ids))
                cursor.execute(delete_content_chunks_sql)
                deleted_count = cursor.rowcount
                print(f"Deleted {deleted_count} content chunks for affected employees.")
            
            
                
            # Bulk insert content chunks for affected employees
            list_of_content_chunks = []
            for emp in valid_employees:
                emp = dict(emp)
                emp['file_data'] = None
                email = emp['email']
                employee_id = next((id for id, e in merge_results if e == email), None)
                if not employee_id:
                    print(f"No employee ID found for email: {email}")
                    continue
                content_chunks = compile_to_chunk(data=emp, employee_id=employee_id, user_id=g.user_id)
                list_of_content_chunks.extend([
                    (chunk['employee_id'], chunk['user_id'], chunk['type'], chunk['chunk_text'])
                    for chunk in content_chunks
                ])

            if list_of_content_chunks:
                insert_content_chunks_sql = """
                    INSERT INTO Content_Chunks (
                        employee_id, user_id, type, chunk_text
                    ) VALUES (
                        %s, %s, %s, %s
                    )
                """
                cursor.executemany(insert_content_chunks_sql, list_of_content_chunks)
                inserted_count = cursor.rowcount
                print(f"Inserted {inserted_count} content chunks for affected employees.")

            # Commit the transaction
            conn.commit()
            final_results = [{"email": emp['email'], **results_map[emp['email']]} for emp in valid_employees if emp['email'] in results_map]
            return jsonify({
                "message": "Bulk employee operation completed using MERGE",
                "results": final_results
            }), 201

        except snowflake.connector.Error as e:
            print(e)
            # Specific Snowflake error handling
            if conn:
                conn.rollback()
            error_msg = f"Snowflake DB Error: {e.errno} ({e.sqlstate}): {e.msg}"
            # Mark all *valid* employees as failed if the MERGE fails
            for emp in valid_employees:
                email_key = emp['email']
                if email_key not in results_map: # Avoid overwriting validation errors
                    results_map[email_key] = {"status": "failed", "error": error_msg}
            final_results = [{"email": k, **v} for k, v in results_map.items()]
            return jsonify({"error": error_msg, "results": final_results}), 400

        except Exception as e:
            print(e)
            # General error handling
            if conn:
                conn.rollback()
            error_msg = f"An unexpected error occurred: {str(e)}"
            for emp in valid_employees:
                email_key = emp['email']
                if email_key not in results_map:
                    results_map[email_key] = {"status": "failed", "error": error_msg}
            final_results = [{"email": k, **v} for k, v in results_map.items()]
            return jsonify({"error": error_msg, "results": final_results}), 400

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 400

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
        },
        401: {'description': 'Unauthorized'},
        500: {'description': 'Internal server error'}
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

