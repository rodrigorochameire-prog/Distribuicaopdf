import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import uuid
import logging

# --- Configuração de Logging ---
LOG_FILE = "setup_drive_webhook.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Configurações --- #
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SOURCE_FOLDER_ID = "1dw8Hfpt_NLtLZ8DYDIcgjauo_xtM1nH4" # ID da pasta no Google Drive onde os PDFs estão

# URL do webhook exposto
WEBHOOK_URL = "https://5000-idawqm7azt7zozvto2ish-a559137e.manusvm.computer/webhook"

# --- Autenticação com Google Drive API --- #
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
            logging.info(f"Por favor, vá para esta URL no seu navegador: {auth_url}")
            
            code = input("Insira o código de autorização obtido do navegador: ")
            
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def setup_webhook_notification(drive_service, folder_id, webhook_url):
    channel_id = str(uuid.uuid4()) # ID único para o canal de notificação
    
    body = {
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_url,
        "token": "your_custom_token_for_validation" # Opcional: token para validar a requisição
    }
    
    try:
        # O método watch é usado para configurar notificações push
        response = drive_service.files().watch(fileId=folder_id, body=body).execute()
        logging.info(f"Notificação push configurada com sucesso para a pasta {folder_id}. Resposta: {response}")
        print(f"Webhook configurado com sucesso! Canal ID: {channel_id}")
        print(f"Por favor, guarde o Canal ID: {channel_id}. Você precisará dele para parar as notificações se necessário.")
    except HttpError as error:
        logging.error(f"Erro ao configurar a notificação push: {error}")
        print(f"Erro ao configurar o webhook: {error}")

if __name__ == '__main__':
    drive_service = authenticate_google_drive()
    logging.info(f"Configurando webhook para a pasta de origem: {SOURCE_FOLDER_ID}")
    setup_webhook_notification(drive_service, SOURCE_FOLDER_ID, WEBHOOK_URL)

