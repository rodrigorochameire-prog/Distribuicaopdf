import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import logging

# --- Configuração de Logging ---
LOG_FILE = "authenticate_google_calendar.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Configurações --- #
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token_calendar.json" # Usar um token separado para o Calendar

# --- Autenticação com Google Calendar API --- #
def authenticate_google_calendar():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_url, _ = flow.authorization_url(prompt='consent')           logging.info(f"Por favor, vá para esta URL no seu navegador: {auth_url}")
            
            code = input("Insira o código de autorização obtido do navegador: ")
            
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

if __name__ == '__main__':
    logging.info("Iniciando processo de autenticação com a Google Calendar API...")
    service = authenticate_google_calendar()
    logging.info("Autenticação com Google Calendar API concluída com sucesso!")
    print("Autenticação com Google Calendar API concluída com sucesso!")

