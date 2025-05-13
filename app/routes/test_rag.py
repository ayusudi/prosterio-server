from flask import Blueprint, request, jsonify
from flasgger import swag_from
from app.db import get_connection
# Import trulens modules correctly
from trulens.core import Tru
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import json
import re

# Download NLTK resources (uncommented to ensure they're installed)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')  # Add this line to download the missing resource

# Initialize TruLens
tru = Tru()

# Custom feedback functions
def custom_groundedness(context, response):
    """Measure if response is grounded in the context"""
    if not context or not response:
        return 0.0
    
    # Simple tokenization without relying on punkt_tab
    context_tokens = set(context.lower().split())
    response_tokens = set(response.lower().split())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    context_tokens = {t for t in context_tokens if t not in stop_words and len(t) > 2}
    response_tokens = {t for t in response_tokens if t not in stop_words and len(t) > 2}
    
    # Calculate overlap
    if not response_tokens:
        return 0.0
    
    overlap = response_tokens.intersection(context_tokens)
    score = len(overlap) / len(response_tokens)
    
    return min(1.0, score)

def custom_relevance(question, response):
    """Measure if response is relevant to the question"""
    if not question or not response:
        return 0.0
    
    # Simple tokenization without relying on punkt_tab
    question_tokens = set(question.lower().split())
    response_tokens = set(response.lower().split())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    question_tokens = {t for t in question_tokens if t not in stop_words and len(t) > 2}
    
    # Calculate overlap
    if not question_tokens:
        return 0.0
    
    overlap = question_tokens.intersection(response_tokens)
    score = len(overlap) / len(question_tokens)
    
    return min(1.0, score)

# Custom Cortex-based evaluator
def cortex_evaluator(question, context, response, conn):
    """Use Cortex to evaluate the response"""
    try:
        cursor = conn.cursor()
        prompt = f"""
        You are an AI assistant evaluating the quality of a response.
        
        CONTEXT: {context}
        
        QUESTION: {question}
        
        RESPONSE: {response}
        
        Rate the response on a scale of 0.0 to 1.0 for the following criteria:
        1. Groundedness: Is the response supported by the context?
        2. Relevance: Is the response relevant to the question?
        3. Coherence: Is the response well-structured and coherent?
        
        Output only a JSON object with the scores, like:
        {{
            "groundedness": 0.85,
            "relevance": 0.92,
            "coherence": 0.78
        }}
        """
        
        cursor.execute("""
        SELECT snowflake.cortex.complete('gemma-7b', %s) AS evaluation
        """, (prompt,))
        
        result = cursor.fetchone()
        evaluation_text = result[0] if result else "{}"
        
        # Extract JSON from the response
        # Find JSON pattern in the text
        json_pattern = r'\{.*\}'
        json_match = re.search(json_pattern, evaluation_text, re.DOTALL)
        
        if json_match:
            try:
                evaluation_json = json.loads(json_match.group())
                return evaluation_json
            except json.JSONDecodeError:
                return {"error": "Failed to parse evaluation JSON"}
        else:
            return {"error": "No JSON found in evaluation response"}
            
    except Exception as e:
        return {"error": str(e)}

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
                            },
                            'evaluation': {
                                'type': 'object',
                                'description': 'TrueLens evaluation metrics'
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
        # Simple approach without context manager
        data = request.json
        question = data.get('prompt')
        conn = get_connection()
        cursor = conn.cursor()
        
        # First, retrieve context
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
        SELECT combined_context FROM concatenated_context;""", (question,))
        
        context_result = cursor.fetchone()
        context = context_result[0] if context_result else ""
        
        # Skip TruLens logging if it's causing issues
        # Just focus on the core RAG functionality
        
        # Generate response using the context
        prompt = f"""Here is our analysis of our employee and recommend their name in your analysis, please just select the related employee who can help to our question. Make sure your narative is explain the project and the reason
        ###
        CONTEXT: {context}
        ###
        QUESTION: {question}
        ANSWER: """
        
        cursor.execute("""
        SELECT snowflake.cortex.complete('gemma-7b', %s) AS response
        """, (prompt,))
        
        result = cursor.fetchone()
        answer = result[0] if result else ""
        
        # Evaluate the response
        eval_results = {}
        
        try:
            # Use NLTK-based evaluators
            grounded_score = custom_groundedness(context, answer)
            eval_results["groundedness"] = float(grounded_score)
            
            relevance_score = custom_relevance(question, answer)
            eval_results["relevance"] = float(relevance_score)
            
            # Optionally, use Cortex for evaluation
            cortex_eval = cortex_evaluator(question, context, answer, conn)
            cortex_coherence = 0.0
            
            if isinstance(cortex_eval, dict) and "error" not in cortex_eval:
                for key, value in cortex_eval.items():
                    if key not in eval_results:  # Don't overwrite existing evaluations
                        eval_results[f"cortex_{key}"] = value
                        if key == "coherence":
                            cortex_coherence = float(value)
            
            # Save evaluation results to database
            cursor.execute("""
            INSERT INTO "PROSTERIO"."PUBLIC"."EVALUATIONS" 
            (question, answer, cortex_coherence, groundedness, relevance, created_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP())
            """, (
                question, 
                answer, 
                cortex_coherence,
                grounded_score,
                relevance_score
            ))
            
            # Commit the transaction
            conn.commit()
            
        except Exception as eval_error:
            print(f"Evaluation error: {eval_error}")
            eval_results["error"] = str(eval_error)
        
        return jsonify({
            "message": "RAG data processed", 
            "answer": answer,
            "evaluation": eval_results
        })
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
