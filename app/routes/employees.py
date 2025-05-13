# --- Imports ---
from flask import Blueprint, request, jsonify, g, send_file, current_app
# Replace psycopg2 with snowflake connector
import snowflake.connector
# Keep json for handling VARIANT data before insertion
import json
# Replace get_connection with your Snowflake connection logic
from app.db import get_connection
from flasgger import swag_from
import json # Import json for handling VARIANT types
import os
from datetime import datetime

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
                    emp.get('id'), # Use None for inserts 0
                    emp['full_name'], # 1
                    emp['email'], # 2
                    emp['job_title'],# 3
                    emp.get('promotion_years'),# 4
                    emp.get('profile'), # 5
                    emp.get('skills'), # Pass Python list directly 6
                    emp.get('professional_experiences'), # Pass Python list of dicts directly 7
                    emp.get('educations'), #8
                    emp.get('publications'), #9
                    emp.get('distinctions'),#10
                    emp.get('certifications'), #11
                    emp.get('file_url'), #12
                    emp['user_id'] #13
                ) for emp in valid_employees
            ]
#  
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
                        PARSE_JSON(v.value[6]::VARCHAR) as skills,
                        PARSE_JSON(v.value[7]::VARCHAR) as professional_experiences,
                        PARSE_JSON(v.value[8]::VARCHAR) as educations,
                        PARSE_JSON(v.value[9]::VARCHAR) as publications,
                        PARSE_JSON(v.value[10]::VARCHAR) as distinctions,
                        PARSE_JSON(v.value[11]::VARCHAR) as certifications,
                        v.value[12]::VARCHAR as file_url,
                        v.value[13]::INTEGER as user_id
                    FROM TABLE(FLATTEN(input => PARSE_JSON(%s))) v
                ) AS source
                ON target.id = source.id OR target.email = source.email
                WHEN MATCHED AND source.id IS NOT NULL THEN
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
                        target.file_url = source.file_url,
                        target.user_id = source.user_id
                WHEN NOT MATCHED THEN
                    INSERT (
                        full_name, email, job_title, promotion_years, profile,
                        skills, professional_experiences, educations,
                        publications, distinctions, certifications,
                        file_url, user_id
                    ) VALUES (
                        source.full_name, source.email, source.job_title, source.promotion_years, source.profile,
                        source.skills, source.professional_experiences, source.educations,
                        source.publications, source.distinctions, source.certifications,
                        source.file_url, source.user_id
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
            SELECT id, full_name, job_title, email, file_url
            FROM employees ORDER BY full_name ASC
        """)
        rows = cursor.fetchall()
        employees = [
            {
                "id": row[0],
                "full_name": row[1],
                "job_title": row[2],
                "email": row[3],
                "file_url": row[4]
            }
            for row in rows
        ]
        return jsonify(employees)
    finally:
        cursor.close()
        conn.close()

@employees_bp.route('/<int:employee_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Delete employee and delete content chunks',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'employee_id', 'in': 'path', 'required': True, 'type': 'integer'}
    ],
    'responses': {
        200: {'description': 'Employee deleted and content chunks removed'},
        404: {'description': 'Employee not found'}
    }
})
def resign_employee(employee_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM content_chunks WHERE employee_id = %s", (employee_id,))
        cursor.execute(f"DELETE FROM employees WHERE id = {employee_id}")
        res = cursor.fetchall()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Employee not found'}), 404
        conn.commit()
        return jsonify({'message': 'Employee resigned and content chunks removed'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@employees_bp.route('/<int:employee_id>', methods=['GET'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Get employee by ID',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'employee_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'description': 'ID of the employee to retrieve'
        }
    ],
    'responses': {
        200: {
            'description': 'Employee details',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
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
                                'date_start': {'type': 'string'},
                                'date_end': {'type': 'string'},
                                'description': {'type': 'string'}
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
                                'score': {'type': 'string'},
                                'date_start': {'type': 'string'},
                                'date_end': {'type': 'string'},
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
                    'file_url': {'type': 'string'},
                }
            }
        },
        404: {'description': 'Employee not found'},
        500: {'description': 'Internal server error'}
    }
})
def get_employee_by_id(employee_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        # Query to get employee by ID and user_id
        cur.execute(f"SELECT id, full_name, email, job_title, promotion_years, profile, skills, professional_experiences, educations, publications, distinctions, certifications, file_url, file_data FROM EMPLOYEES WHERE ID = {employee_id}")
        employees = cur.fetchall()
        if not employees:
            return jsonify({"error": "Employee not found"}), 404
        employee = employees[0]
        # Create response without file_data first
     
        file_url = employee[12]
        # If file_data exists, save it to public folder and update URL
        if employee[13] is not None:
            try:
                # Convert to bytes if it's a bytearray
                file_bytes = bytes(employee[13]) if isinstance(employee[13], bytearray) else employee[13]
                
                # Create public folder if it doesn't exist
                public_folder = os.path.join(current_app.root_path, 'public', 'pdfs')
                os.makedirs(public_folder, exist_ok=True)
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"employee_{employee_id}_{timestamp}.pdf"
                filepath = os.path.join(public_folder, filename)
                
                # Save the file
                with open(filepath, 'wb') as f:
                    f.write(file_bytes)
                
                # Update the file_url in the database
                file_url = f"{request.scheme}://{request.host}/static/pdfs/{filename}"
                
            except Exception as e:
                print(f"Error handling file data: {str(e)}")
                return jsonify({"error": "Error processing file data"}), 500
        
        result = {
            "id": employee[0],
            "full_name": employee[1],
            "email": employee[2],
            "job_title": employee[3],
            "promotion_years": employee[4],
            "profile": employee[5],
            "skills": json.loads(employee[6]),
            "professional_experiences": json.loads(employee[7]),
            "educations": json.loads(employee[8]),
            "publications": json.loads(employee[9]),
            "distinctions": json.loads(employee[10]),
            "certifications": json.loads(employee[11]),
            "file_url": file_url
        }
        return jsonify(result)
    except Exception as e:
        print(e)
        print(f"Error getting employee: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        cur.close()
        conn.close()

@employees_bp.route('/<int:employee_id>', methods=['PUT'])
@swag_from({
    'tags': ['Employees'],
    'summary': 'Update employee by ID',
    'description': 'Update employee information excluding file_url and file_data',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'employee_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID of the employee to update'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'full_name': {'type': 'string', 'description': 'Full name of the employee'},
                    'email': {'type': 'string', 'description': 'Email address'},
                    'job_title': {'type': 'string', 'description': 'Current job title'},
                    'promotion_years': {'type': 'integer', 'description': 'Years until promotion'},
                    'profile': {'type': 'string', 'description': 'Employee profile/bio'},
                    'skills': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'List of skills'
                    },
                    'professional_experiences': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'company': {'type': 'string'},
                                'job_title': {'type': 'string'},
                                'date_start': {'type': 'string'},
                                'date_end': {'type': 'string'},
                                'description': {'type': 'string'}
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
                                'score': {'type': 'string'},
                                'date_start': {'type': 'string'},
                                'date_end': {'type': 'string'},
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
                    'certifications': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                },
                'required': ['full_name', 'email', 'job_title']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Employee updated successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'employee_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Employee not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Internal server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def update_employee_by_id(employee_id):
    """Update employee details by ID"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'job_title']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        conn = get_connection()
        cur = conn.cursor()
        
        # Check if employee exists
        cur.execute(f"SELECT id FROM EMPLOYEES WHERE ID = {employee_id}")
        if not cur.fetchone():
            return jsonify({"error": "Employee not found"}), 404

        # Prepare update fields and values separately for VARIANT fields
        variant_fields = {
            'skills': data.get('skills', []),
            'professional_experiences': data.get('professional_experiences', []),
            'educations': data.get('educations', []),
            'publications': data.get('publications', []),
            'distinctions': data.get('distinctions', []),
            'certifications': data.get('certifications', [])
        }
        
        # Regular fields
        regular_fields = {
            'full_name': data.get('full_name'),
            'email': data.get('email'),
            'job_title': data.get('job_title'),
            'promotion_years': data.get('promotion_years'),
            'profile': data.get('profile')
        }
        
        try:
            # Build update query with proper Snowflake VARIANT handling
            variant_updates = []
            for key, value in variant_fields.items():
                json_str = json.dumps(value)
                variant_updates.append(f"{key} = PARSE_JSON(TO_VARCHAR({json_str}))")
            
            # Handle regular fields
            regular_updates = []
            for key, value in regular_fields.items():
                if value is not None:
                    escaped_value = str(value).replace("'", "''")
                    regular_updates.append(f"{key} = '{escaped_value}'")
                else:
                    regular_updates.append(f"{key} = NULL")
            
            # Combine both clauses
            set_clause = ", ".join(regular_updates + variant_updates)
            
            
            # Execute update
            cur.execute("""
                UPDATE Employees SET
                    full_name = %s,
                    email = %s,
                    job_title = %s,
                    promotion_years = %s,
                    profile = %s,
                    skills = %s,
                    professional_experiences = %s,
                    educations = %s,
                    publications = %s,
                    distinctions = %s,
                    certifications = %s,
                    user_id = %s,
                    updated_at = CURRENT_TIMESTAMP()
                WHERE ID = %s
            """, (data['full_name'], data['email'], data['job_title'], data['promotion_years'], data['profile'], json.dumps(data['skills']), json.dumps(data['professional_experiences']), json.dumps(data['educations']), json.dumps(data['publications']), json.dumps(data['distinctions']), json.dumps(data['certifications']), g.user_id, employee_id))
            res = cur.fetchall()
            # Update content chunks with proper escaping
            cur.execute(f"DELETE FROM Content_Chunks WHERE employee_id = {employee_id}")
            
            # Create new content chunks
            content_chunks = compile_to_chunk(data=data, employee_id=employee_id, user_id=g.user_id)
            
            # Insert new chunks with proper escaping
            chunk_values = []
            for chunk in content_chunks:
                chunk_text = chunk['chunk_text'].replace("'", "''")
                chunk_type = chunk['type'].replace("'", "''")
                chunk_values.append(f"""(
                    {chunk['employee_id']}, 
                    {g.user_id}, 
                    '{chunk_type}', 
                    '{chunk_text}'
                )""")
            
            if chunk_values:
                chunks_insert_query = f"""
                    INSERT INTO Content_Chunks (employee_id, user_id, type, chunk_text)
                    VALUES {', '.join(chunk_values)}
                """
                cur.execute(chunks_insert_query)
            
            conn.commit()
            return jsonify({
                "message": "Employee updated successfully",
                "employee_id": employee_id
            }), 200
            
        except json.JSONDecodeError as e:
            print(f"JSON Error: {str(e)}")
            if conn:
                conn.rollback()
            return jsonify({"error": "Invalid JSON data provided"}), 400
        except Exception as e:
            print(f"Error processing update: {str(e)}")
            if conn:
                conn.rollback()
            return jsonify({"error": "Error processing update"}), 500
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Internal server error"}), 500
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

