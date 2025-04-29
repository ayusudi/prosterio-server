from flask import Blueprint, jsonify
from app.db import get_connection
from flasgger import swag_from

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics', methods=['GET'])
@swag_from({
    'tags': ['Analytics'],
    'summary': 'Get various analytics data',
    'responses': {
        200: {
            'description': 'Analytics data retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'job_title_distribution': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'job_title': {'type': 'string'},
                                'total_employees': {'type': 'integer'}
                            }
                        }
                    },
                    'experience_level_distribution': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'experience_level': {'type': 'string'},
                                'total_employees': {'type': 'integer'}
                            }
                        }
                    },
                    'top_skills': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'skill': {'type': 'string'},
                                'total_employees': {'type': 'integer'}
                            }
                        }
                    },
                    'education_to_job_title': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'education': {'type': 'string'},
                                'job_title': {'type': 'string'},
                                'count': {'type': 'integer'}
                            }
                        }
                    }
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
def get_analytics():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Job Title Distribution
        cursor.execute("""
            SELECT JOB_TITLE, COUNT(*) AS total_employees 
            FROM Employees 
            GROUP BY JOB_TITLE 
            ORDER BY total_employees DESC
        """)
        job_title_distribution = [{'job_title': row[0], 'total_employees': row[1]} for row in cursor.fetchall()]

        # Experience Level Distribution
        cursor.execute("""
            SELECT 
              CASE 
                WHEN JOB_TITLE ILIKE '%Junior%' THEN 'Junior' 
                WHEN JOB_TITLE ILIKE '%Senior%' THEN 'Senior' 
                WHEN JOB_TITLE ILIKE '%Manager%' THEN 'Managerial' 
                ELSE 'Mid-Level' 
              END AS experience_level, 
              COUNT(*) AS total_employees 
            FROM Employees 
            GROUP BY experience_level
        """)
        experience_level_distribution = [{'experience_level': row[0], 'total_employees': row[1]} for row in cursor.fetchall()]

        # Top Skills
        cursor.execute("""
            SELECT 
              TRIM(f.value::STRING, '"') AS skill, 
              COUNT(*) AS total_employees 
            FROM Employees, 
            LATERAL FLATTEN(input => PARSE_JSON(SKILLS)) f 
            GROUP BY skill 
            ORDER BY total_employees DESC 
            LIMIT 10
        """)
        top_skills = [{'skill': row[0], 'total_employees': row[1]} for row in cursor.fetchall()]

        # Education to Job Title Distribution
        cursor.execute("""
            SELECT edu.value:title::STRING AS education, JOB_TITLE, COUNT(*) AS count 
            FROM Employees, LATERAL FLATTEN(input => PARSE_JSON(EDUCATIONS)) edu 
            GROUP BY education, JOB_TITLE
        """)
        education_to_job_title = [{'education': row[0], 'job_title': row[1], 'count': row[2]} for row in cursor.fetchall()]

        return jsonify({
            'job_title_distribution': job_title_distribution,
            'experience_level_distribution': experience_level_distribution,
            'top_skills': top_skills,
            'education_to_job_title': education_to_job_title
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Don't forget to register this blueprint in your main app file