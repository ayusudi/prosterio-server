from flask import Blueprint, request, jsonify
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os, tempfile, re, json

load_dotenv()
documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

# Prompt template to guide Gemini
PROMPT_TEMPLATE = """
Extract structured data from this CV text in JSON with the following fields:
- full_name
- email
- job_titles
- promotion_years (as integer)
- profile
- skills (as list of strings)
- professional_experiences (list)
- educations (list)
- publications (list)
- distinctions (list)
- certifications (list)

Return only valid JSON with no explanation or markdown.

Here is the CV text:
\"\"\"
{text}
\"\"\"
"""

@documents_bp.route('', methods=["POST"])
def extract_with_gemini():
    """
    Upload and extract structured CV data from one or more PDF files using Gemini

    ---
    tags:
      - Documents
    consumes:
      - multipart/form-data
    parameters:
      - name: documents
        in: formData
        type: file
        required: true
        description: Upload one or more PDF files
        collectionFormat: multi
    responses:
      200:
        description: A list of extracted CV data or errors per file
        schema:
          type: array
          items:
            type: object
            properties:
              filename:
                type: string
              data:
                type: object
              error:
                type: string
      400:
        description: No PDF files uploaded
      500:
        description: Internal server error or Gemini failure
    """
    uploaded_files = request.files.getlist("documents")
    if not uploaded_files:
        return jsonify({"error": "No PDF files uploaded"}), 400

    gemini_api_key = os.getenv("GEMINI_APIKEY")
    if not gemini_api_key:
        return jsonify({"error": "GEMINI_APIKEY not found"}), 500

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")

        results = []

        for uploaded_file in uploaded_files:
            try:
                with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
                    uploaded_file.save(tmp.name)

                    loader = PyPDFLoader(tmp.name)
                    pages = loader.load_and_split()
                    text = " ".join([page.page_content.strip() for page in pages])

                prompt = PROMPT_TEMPLATE.format(text=text)
                response = model.generate_content(prompt)
                response_text = response.text.strip()

                # Safely extract JSON block from LLM response
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if not match:
                    raise ValueError("No valid JSON found in Gemini response.")

                json_data = json.loads(match.group(0))
                results.append({
                    "filename": uploaded_file.filename,
                    "data": json_data
                })

            except Exception as file_error:
                results.append({
                    "filename": uploaded_file.filename,
                    "error": str(file_error)
                })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
