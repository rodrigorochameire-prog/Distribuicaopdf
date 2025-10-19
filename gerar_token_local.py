import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Defina os escopos necessários para Calendar e Drive
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/drive']

# O caminho para o seu arquivo credentials.json (baixe do Google Cloud Console)
# Certifique-se de que este arquivo está na mesma pasta onde você vai rodar este script
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def main():
    creds = None
    # O arquivo token.json armazena os tokens de acesso e refresh do usuário,
    # e é criado automaticamente quando o fluxo de autorização é concluído pela primeira vez.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há credenciais válidas disponíveis, o usuário precisa fazer login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Certifique-se de que o arquivo credentials.json está presente
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Erro: O arquivo '{CREDENTIALS_FILE}' não foi encontrado.")
                print("Por favor, baixe seu 'credentials.json' do Google Cloud Console ")
                print("e coloque-o na mesma pasta deste script.")
                return

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Salva as credenciais para a próxima execução
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    print(f"\n✅ Arquivo '{TOKEN_FILE}' gerado com sucesso!")
    print("Por favor, envie este arquivo de volta para o Manus.")

if __name__ == '__main__':
    main()

