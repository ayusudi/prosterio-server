from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import os
# --- Imports ---
from flask import Blueprint, request, jsonify
# Replace get_connection with your Snowflake connection logic
from flasgger import swag_from
from dotenv import load_dotenv

load_dotenv()

gdrive_bp = Blueprint('gdrive', __name__, url_prefix='/api/gdrive')

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """Get Google Drive service instance."""
    # Load credentials from service account info
    credentials_info = {
        "type": "service_account",
        "project_id": os.getenv('GOOGLE_PROJECT_ID'),
        "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
        "private_key": os.getenv('GOOGLE_PRIVATE_KEY'),
        "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
        "client_id":os.getenv('GOOGLE_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "",
        "universe_domain": "googleapis.com",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES
    )
   
    return build('drive', 'v3', credentials=credentials)

@gdrive_bp.route('', methods=['POST'])
@swag_from({
    'tags': ['Gdrive'],
    'summary': 'Upload file to Google Drive',
    'description': 'Upload a file to Google Drive and make it publicly accessible',
    'security': [{'Bearer': []}],
    'parameters': [
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'File to upload (PDF)'
        },
        {
            'name': 'file_name',
            'in': 'formData',
            'type': 'string',
            'required': True,
            'description': 'Name of the file'
        }
    ],
    'responses': {
        200: {
            'description': 'File uploaded successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'file_id': {'type': 'string', 'description': 'Google Drive file ID'},
                    'web_view_link': {'type': 'string', 'description': 'Public URL to view the file'}
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
        401: {
            'description': 'Unauthorized - Invalid or missing token',
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
def upload_file():
    """Upload file to Google Drive endpoint"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        file_name = request.form.get('file_name')
        
        if not file_name:
            return jsonify({'error': 'No file name provided'}), 400
            
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Read file data
        file_data = file.read()
        
        # Upload to Google Drive
        result = upload_to_drive(file_data, file_name)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def upload_to_drive(file_data, file_name, mime_type='application/pdf'):
    """
    Upload file to Google Drive and make it publicly accessible.
    
    Args:
        file_data: Binary file data
        file_name: Name of the file
        mime_type: MIME type of the file
        
    Returns:
        dict: Contains file_id and web_view_link
    """
    try:
        drive_service = get_google_drive_service()
        
        # Create file metadata
        file_metadata = {
            'name': file_name,
            'parents': [os.getenv('GOOGLE_DRIVE_FOLDER_ID')]
        }
        
        # Create media object
        media = MediaIoBaseUpload(
            io.BytesIO(file_data),
            mimetype=mime_type,
            resumable=True
        )
        
        # Upload file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        # Make file publicly accessible
        drive_service.permissions().create(
            fileId=file['id'],
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        return {
            'file_id': file['id'],
            'web_view_link': file['webViewLink']
        }
        
    except Exception as e:
        print(f"Error uploading to Google Drive: {str(e)}")
        raise
    
    # 