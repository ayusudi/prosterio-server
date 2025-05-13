from flask import Blueprint, request, jsonify
from groq import Groq
import os, time
from flasgger import swag_from
from langsmith import Client
from langsmith.run_trees import RunTree
import traceback  # Tambahkan untuk debugging yang lebih baik
from dotenv import load_dotenv
import uuid
import json
from app.db import get_connection

# Inisialisasi Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

prompt_bp = Blueprint('prompt', __name__, url_prefix='/api')

# System prompt tetap sama seperti sebelumnya
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

# Fungsi untuk menyimpan data ke Snowflake
def log_to_snowflake(run_id, timestamp, user_input, response, latency, token_count, model, status="success", error=None):
    try:
        # Buat koneksi ke Snowflake
        conn = get_connection()
        
        # Buat cursor
        cursor = conn.cursor()
        
        # Siapkan kueri SQL
        query = """
        INSERT INTO LLM_EVALUATIONS (
            RUN_ID, 
            TIMESTAMP, 
            USER_INPUT, 
            MODEL_RESPONSE, 
            LATENCY_SECONDS, 
            TOKEN_COUNT, 
            MODEL_NAME, 
            STATUS,
            ERROR_MESSAGE
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Eksekusi kueri
        cursor.execute(
            query, 
            (
                run_id, 
                timestamp, 
                user_input, 
                response, 
                latency, 
                token_count, 
                model, 
                status, 
                error
            )
        )
        
        # Commit perubahan
        conn.commit()
        
        # Tutup cursor dan koneksi
        cursor.close()
        conn.close()
        
        print(f"Data berhasil disimpan ke Snowflake dengan run_id: {run_id}")
        return True
        
    except Exception as e:
        print(f"Error menyimpan data ke Snowflake: {str(e)}")
        return False

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

        # Generate run ID unik
        run_id = str(uuid.uuid4())
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        initialize = [{"role": "system", "content": text_system}]
        messages = initialize + data['chats']
        
        # Ekstrak input pengguna terakhir
        user_input = data['chats'][-1]['content'] if data['chats'] else ""
        max_tokens = data.get('max_token', 512)
        
        # Waktu mulai untuk mengukur latency
        start_time = time.time()
        
        try:
            # Panggil API Groq
            response = client.chat.completions.create(
                model="gemma2-9b-it",
                messages=messages,
                max_tokens=max_tokens,
                stream=False,
            )
            
            # Hitung metrik
            latency = time.time() - start_time
            output_content = response.choices[0].message.content
            token_count = len(output_content.split())  # Estimasi kasar jumlah token
            
            # Log informasi debugging
            print(f"User input: {user_input[:50]}...")
            print(f"Response time: {latency:.2f}s")
            
            # Log ke Snowflake secara asynchronous
            # Dalam aplikasi produksi, gunakan threading atau task queue
            log_to_snowflake(
                run_id=run_id,
                timestamp=timestamp,
                user_input=user_input,
                response=output_content,
                latency=latency,
                token_count=token_count,
                model="gemma2-9b-it"
            )
            
            return jsonify({
                "message": "Prompt received",
                "response": output_content,
                "metrics": {
                    "run_id": run_id,
                    "latency_seconds": latency,
                    "estimated_token_count": token_count
                }
            })
            
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"Groq API error: {error_msg}")
            
            # Log error ke Snowflake
            log_to_snowflake(
                run_id=run_id,
                timestamp=timestamp,
                user_input=user_input,
                response=None,
                latency=time.time() - start_time,
                token_count=0,
                model="gemma2-9b-it",
                status="error",
                error=error_msg
            )
                
            return jsonify({"error": error_msg}), 500
            
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({"error": str(e)}), 500