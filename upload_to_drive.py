
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def authenticate_google_drive():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"Por favor, vá para esta URL no seu navegador: {auth_url}")
            code = input("Insira o código de autorização obtido do navegador: ")
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def upload_file(drive_service, filepath, folder_id):
    filename = os.path.basename(filepath)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, mimetype='application/pdf')
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Arquivo '{filename}' com ID: {file.get('id')} enviado para a pasta {folder_id}.")

if __name__ == '__main__':
    drive_service = authenticate_google_drive()
    SOURCE_FOLDER_ID = "1dw8Hfpt_NLtLZ8DYDIcgjauo_xtM1nH4" # ID da pasta de origem
    # Certifique-se de que dummy_processo.pdf existe no diretório atual
    upload_file(drive_service, "dummy_processo.pdf", SOURCE_FOLDER_ID)

