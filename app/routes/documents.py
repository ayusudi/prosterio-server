from flask import Blueprint, request, jsonify
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import os, tempfile, re, json
from app.db import get_connection

load_dotenv()
documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")

# Prompt template to guide Gemini
PROMPT_TEMPLATE = """
**Only extract data that appears in the CV text; do not invent or infer missing details. Use null for any missing single-value field and an empty list [] for any missing array. Strictly adhere to the date formats and data types described above.**
Extract structured data from this CV text in JSON with the following fields:
- full_name
- email
- job_title 
- promotion_years (as integer)
- profile
- skills (as list of strings)
- professional_experiences (list)
- educations (list)
- publications (list)
- distinctions (list)
- certifications (list)

for promotion_years is year of the first job she/he got

for professional_experiences:
- company
- job_title
- date_start (MMM YYYY)
- date_end (MMM YYYY or "Current)
- description

for educations:
- institution
- title
- score (score/max_score)
- date_start (YYYY)
- date_end (YYYY or "Current)
- description

for publications:
- name
- description
- link

for distinctions:
- name
- description

for certifications is list of text (short title of certification, issuer and date issue)

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
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  filename:
                    type: string
                  data:
                    type: object
                    properties:
                      full_name:
                        type: string
                      email:
                        type: string
                      job_title:
                        type: string
                      promotion_years:
                        type: integer
                      profile:
                        type: string
                      skills:
                        type: array
                        items:
                          type: string
                      professional_experiences:
                        type: array
                        items:
                          type: object
                          properties:
                            company:
                              type: string
                            job_title:
                              type: string
                            date_start:
                              type: string
                            date_end:
                              type: string
                            description:
                              type: string
                      educations:
                        type: array
                        items:
                          type: object
                          properties:
                            institution:
                              type: string
                            title:
                              type: string
                            score:
                              type: string
                            date_start:
                              type: string
                            date_end:
                              type: string
                            description:
                              type: string
                      publications:
                        type: array
                        items:
                          type: object
                          properties:
                            name:
                              type: string
                            description:
                              type: string
                            link:
                              type: string
                      distinctions:
                        type: array
                        items:
                          type: object
                          properties:
                            name:
                              type: string
                            description:
                              type: string
                      certifications:
                        type: array
                        items:
                          type: string
                  error:
                    type: string
            email_status:
              type: object
              additionalProperties:
                type: boolean
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
        emails = []
        
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
                if json_data.get("email"):
                  email = json_data.get('email')
                  emails.append(email)
                  
                results.append({
                    "filename": uploaded_file.filename,
                    "data": json_data
                })

            except Exception as file_error:
                results.append({
                    "filename": uploaded_file.filename,
                    "error": str(file_error)
                })
                
        email_status = {}
        if emails:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT email 
                    FROM Employees 
                    WHERE email IN ({})
                """.format(','.join(['%s'] * len(emails))), emails)
                email_status = {email: False for email in emails}
                for row in cursor.fetchall():
                    email_status[row[0]] = True
            finally:
                cursor.close()
                conn.close()

        return jsonify({"data": results, "email_status": email_status}), 200

    except Exception as e:
      
        return jsonify({"error": str(e)}), 500
