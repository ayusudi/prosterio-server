from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.db import get_connection
rag_bp = Blueprint('rag', __name__, url_prefix='/api')
    
@rag_bp.route('/rag', methods=['POST'])
@swag_from({
    'tags': ['RAG'],
    'description': 'Process RAG (Retrieval-Augmented Generation) query',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'prompt': {
                        'type': 'string',
                        'description': 'The question to be answered'
                    }
                },
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'RAG data processed successfully',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {
                                'type': 'string',
                                'description': 'Status message'
                            },
                            'answer': {
                                'type': 'string',
                                'description': 'Generated answer from the RAG query'
                            }
                        }
                    }
                }
            }
        },
        '500': {
            'description': 'Internal server error',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'error': {
                                'type': 'string',
                                'description': 'Error message'
                            }
                        }
                    }
                }
            }
        }
    }
})
def handle_rag():
    try:
        data = request.json
        question = data.get('prompt')
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        WITH context AS (
            SELECT employee_id, chunk_text, snowflake.cortex.embed_text_1024('snowflake-arctic-embed-l-v2.0', chunk_text) AS embedding
            FROM "PROSTERIO"."PUBLIC"."CONTENT_CHUNKS"
            QUALIFY ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY employee_id) = 1
            ORDER BY vector_cosine_similarity(embedding, snowflake.cortex.embed_text_1024('snowflake-arctic-embed-l-v2.0', %s)) DESC
        ),
        concatenated_context AS (
            SELECT LISTAGG(chunk_text, ' ') WITHIN GROUP (ORDER BY employee_id) AS combined_context FROM context
        )
        SELECT 
                snowflake.cortex.complete(
                    'gemma-7b', 
                    'Here is our analysis of our employee and recommend their name in your analysis, please just select the related employee who can help to our question. Make sure your narative is explain the project and the reason ' || 
                    '###
                    CONTEXT: ' || concatenated_context.combined_context || '
                    ###
                    QUESTION: ' || %s || '
                    ANSWER: '
                ) AS response
        FROM concatenated_context;""", (question, question))
        result = cursor.fetchone()
        print(result)
        return jsonify({"message": "RAG data processed", "answer": result[0]})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
