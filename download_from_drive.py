import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

def download_file(service, file_id, file_name, destination_path):
    try:
        request = service.files().get_media(fileId=file_id)
        with open(os.path.join(destination_path, file_name), 'wb') as f:
            f.write(request.execute())
        print(f"Arquivo '{file_name}' (ID: {file_id}) baixado com sucesso para {destination_path}")
    except HttpError as error:
        print(f"Ocorreu um erro ao baixar o arquivo '{file_name}': {error}")

import sys

if __name__ == '__main__':
    drive_service = authenticate_google_drive()
    if len(sys.argv) != 3:
        print("Uso: python3 download_from_drive.py <file_id> <destination_path>")
        sys.exit(1)
    
    file_id = sys.argv[1]
    destination_path = sys.argv[2]
    
    # Obter o nome do arquivo do Drive
    try:
        file_metadata = drive_service.files().get(fileId=file_id, fields='name').execute()
        file_name = file_metadata.get('name')
    except HttpError as error:
        print(f"Ocorreu um erro ao obter o nome do arquivo (ID: {file_id}): {error}")
        sys.exit(1)

    if file_name:
        download_file(drive_service, file_id, file_name, destination_path)
    else:
        print(f"Não foi possível obter o nome do arquivo para o ID: {file_id}")

