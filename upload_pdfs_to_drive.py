import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SOURCE_FOLDER_ID = "1dw8Hfpt_NLtLZ8DYDIcgjauo_xtM1nH4"

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

def upload_pdf_to_drive(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Arquivo '{file_name}' (ID: {file.get('id')}) enviado com sucesso para a pasta de origem.")
    except HttpError as error:
        print(f"Ocorreu um erro ao enviar o arquivo '{file_name}': {error}")

def main():
    drive_service = authenticate_google_drive()
    local_pdf_files = [f for f in os.listdir('/home/ubuntu/') if f.endswith('.pdf')]
    
    for pdf_file in local_pdf_files:
        upload_pdf_to_drive(drive_service, os.path.join('/home/ubuntu/', pdf_file), SOURCE_FOLDER_ID)

if __name__ == '__main__':
    main()
