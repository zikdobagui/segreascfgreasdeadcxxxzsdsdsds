# gdrive_uploader.py
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_FILE", "credentials.json")
BACKUP_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", None)

def upload_to_drive(file_path: str) -> str:
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    metadata = {'name': os.path.basename(file_path)}
    if BACKUP_FOLDER_ID:
        metadata['parents'] = [BACKUP_FOLDER_ID]
    media = MediaFileUpload(file_path, mimetype='application/zip', resumable=True)
    created = service.files().create(body=metadata, media_body=media, fields='id').execute()
    file_id = created.get('id')
    service.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()
    return f"https://drive.google.com/file/d/{file_id}/view"
