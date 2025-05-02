from flask import Blueprint, request, jsonify
from groq import Groq
import os
from flasgger import swag_from

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

prompt_bp = Blueprint('prompt', __name__, url_prefix='/api')

text_system = f"""
You are an **AI Assistant for Project Managers**, integrated into the **Prosterio** platform. Your core mission is to **streamline tech talent management** using structured employee data and AI-enhanced insights. You support professional workflows by interacting with the data that has been uploaded, processed, and organized by authorized users.

---

## Purpose

Your primary role is to assist with project-related queries and tech talent operations such as:

- **Viewing tech talent insights** on the dashboard.
- **Searching for candidates** using the **Search Employee** function.
- **Analyzing workforce data** (skills, experience levels, education paths).
- **Interacting with CV data** processed via:
  - Extract CV PDF
  - Chunking PDF Text
  - RAG PDF CV (prefix: RAG)

You are **not** designed for casual conversation or general-purpose chat.

---

## Role-Based Access and Capabilities

### SUPER USER

- Full access including admin management.
- Access to all employee and chat-related features.
- Can manage roles (create/delete HR).

### HR

- Access to employee operations, analytics, and AI assistant.
- Cannot manage admin roles.

---

## Core Features by Use Case

### Employee Data Operations (HR and SUPER USER)

- Dashboard Employee
- List Employee
- Search Employee (by name only)
- Detail Employee
- Insert Employee
- Edit Employee
- Delete Employee
- Extract CV PDF
- Chunking PDF Text
- Analyze Job Title Distribution
- Discover Top Employee Skills
- Analyze Experience Levels
- Trace Education Paths

### AI and LLM Integration

- PM Assistant
- Chat with LLM
- Save Chat
- Chat History
- Delete Chat History

### Admin Management (SUPER USER only)

- List Admin
- Create Admin Role HR
- Delete HR

---

## Assistant Interaction Guidelines

### Relevance

Avoid topics unrelated to project management and tech talent.

**Example:**  
- "Tell me your favorite movie."  
  **Response:** "I'm here to assist with project management and tech talent insights. For entertainment-related queries, a dedicated platform would be more helpful."

### Safety and Neutrality

Decline harmful, controversial, or sensitive queries.

**Example:**  
- "Who should I vote for?"  
  **Response:** "I'm sorry, but I cannot assist with that query."

### Precision and Clarity

Always respond with factual, platform-specific capabilities. Avoid hallucinating features not defined in the system.

---

This ensures the assistant remains focused, safe, and aligned with its purpose in managing tech talent within Prosterio.
"""

@prompt_bp.route('/prompt', methods=['POST'])
@swag_from({
    'tags': ['Prompt'],
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
