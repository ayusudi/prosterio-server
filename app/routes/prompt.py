from flask import Blueprint, request, jsonify
from groq import Groq
import os
from flasgger import swag_from

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

prompt_bp = Blueprint('prompt', __name__, url_prefix='/api')

text_system = f"""
You are an AI Assistant for Project Managers, designed to streamline tech talent management through the application named Prosterio. You assist with tasks such as searching for candidates based on tech talent data uploaded by the user via the 'Add IT Talent' feature or viewing talent on the dashboard page.

Purpose: Respond professionally and focus strictly on topics relevant to project management and tech talent.

Guidelines:

Relevance: Avoid providing detailed responses to unrelated topics, such as movies, personal questions, or casual chats. Politely redirect the user to ask questions within your domain expertise.

Safety: Ensure responses are safe, respectful, and neutral, avoiding harm or controversial topics.

Clarity: Provide clear, concise, and professional responses to maintain the credibility of the assistant.

Examples:

If asked about movies: "I'm here to assist with project management and tech talent tasks. For movie-related queries, I recommend consulting a dedicated platform."

If asked a potentially harmful or controversial question: "I'm sorry, but I cannot assist with that query."

This ensures that the assistant remains focused, safe, and aligned with its purpose.
"""

@prompt_bp.route('/prompt', methods=['POST'])
@swag_from({
    'tags': ['prompt'],
    'description': 'Process a prompt and get AI response',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'chats': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'role': {'type': 'string'},
                                'content': {'type': 'string'}
                            }
                        }
                    },
                    'max_token': {
                        'type': 'integer',
                        'description': 'Maximum number of tokens to generate'
                    }
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Success',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'response': {'type': 'string'}
                }
            }
        },
        '400': {
            'description': 'Bad Request'
        },
        '500': {
            'description': 'Internal Server Error'
        }
    }
})
def handle_prompt():
    try:
        data = request.json
        if not data or 'chats' not in data:
            return jsonify({"error": "Invalid request format"}), 400

        initialize = [{"role": "system", "content": text_system}]
        messages = initialize + data['chats']
        
        # Get max_token from request data, default to 1000 if not provided
        max_tokens = data.get('max_token', 512)
        
        response = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=messages,
            max_tokens=max_tokens,
            stream=False,
        )
        
        return jsonify({
            "message": "Prompt received",
            "response": response.choices[0].message.content
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
