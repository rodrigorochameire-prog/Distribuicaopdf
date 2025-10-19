#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import unicodedata
import logging
from PyPDF2 import PdfReader
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuração de Logging --- #
LOG_FILE = "automação_distribuição_pdfs.log"
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
CREDENTIALS_FILE = "credentials.json"  # Arquivo de credenciais do Google API
TOKEN_FILE = "token.json"              # Arquivo para armazenar o token de acesso
SOURCE_FOLDER_ID = "1dw8Hfpt_NLtLZ8DYDIcgjauo_xtM1nH4" # ID da pasta no Google Drive onde os PDFs estão
ROOT_DESTINATION_FOLDER_ID = "1fN2GiGlNzc61g01ZeBMg9ZBy1hexx0ti" # ID da pasta raiz onde as pastas das varas serão criadas (Processos - VVD)
DYNAMIC_COURT_ROOT_FOLDER_ID = "1bxPN_PF-wC0XNX79UXCSi5UVDuIHt5Lf" # ID da pasta raiz para criação dinâmica de pastas de comarcas

# --- Mapeamento de Órgãos Julgadores para Nomes de Pastas --- #
# Adicione aqui outros mapeamentos conforme necessário
COURT_FOLDER_MAPPING = {
    "VARA DE VIOLÊNCIA DOMÉSTICA FAM CONTRA A MULHER DE CAMAÇARI": "Processos - VVD",
    "VARA DO JÚRI E EXECUÇÕES PENAIS DA COMARCA DE CAMAÇARI": "1_S-2qdqO0n1npNcs0PnoagBM4ZtwKhk-",
    # Exemplo: "Outro Órgão Julgador": "Processos - Outra Vara",
}

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
            
            # Solicita ao usuário que insira o código de autorização manualmente
            code = input("Insira o código de autorização obtido do navegador: ")
            
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

# --- Extração de nome do assistido e órgão julgador do PDF --- #
def extract_info_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        
        assisted_name = None
        court_name = None

        # --- Função auxiliar para processar o nome do assistido --- #
        def process_assisted_name(name_candidate_str):
            if not name_candidate_str:
                return None
            # Normaliza caracteres Unicode para garantir consistência (ex: decompor caracteres acentuados)
            name_candidate_str = unicodedata.normalize('NFKC', name_candidate_str)
            # Remove caracteres que não são letras (incluindo acentuadas), espaços ou hífens
            # O padrão \p{L} no regex com flags=re.UNICODE permite casar com qualquer tipo de letra Unicode.
            # Mantém o hífen para nomes compostos.
            # Substituindo \p{L} por um padrão compatível com re que inclua caracteres Unicode
            # Isso remove caracteres que não são letras (incluindo acentuadas), espaços ou hífens.
            # O re.UNICODE flag já está definido para o módulo, mas \p{L} não é diretamente suportado.
            # Uma alternativa é usar [^\W\d_] que com re.UNICODE inclui letras Unicode, ou especificar ranges.
            # Para garantir a preservação de acentos, vamos usar um regex que remove tudo que não é letra, espaço ou hífen.
            # A regex [^\w\s-] com re.UNICODE já deve funcionar para a maioria dos casos.
            # No entanto, para ser mais explícito e evitar o problema de \p{L}, usaremos uma abordagem mais simples e direta.
            # O erro `bad escape \p` indica que \p{L} não é interpretado corretamente.
            # Uma forma mais robusta é usar o próprio re.UNICODE para \w que cobre letras.
            # Vamos tentar [^\W\d_\s-] que permite letras, espaços e hífens.
            # Ou, se o problema for com \p{L}, podemos usar um conjunto de caracteres mais abrangente.
            # Vou usar uma abordagem mais simples que remove caracteres que não são alfanuméricos, espaços ou hífens.
            # O re.UNICODE já afeta \w, então [^\W\s-] deve ser suficiente para manter letras e acento            name_candidate_str = re.sub(r'[^\w\s-]', '', name_candidate_str, flags=re.UNICODE)       # Remove múltiplos espaços e espaços no início/fim
            name_candidate_str = re.sub(r'\s+', ' ', name_candidate_str).strip()
            # Capitaliza a primeira letra de cada palavra, preservando acentos
            # Usamos title() diretamente aqui, pois unicodedata.normalize ajuda a lidar com os acentos
            return name_candidate_str.title()

        # Extração do nome do assistido (primeira tentativa com padrões prioritários)
        patterns_assisted_name_primary = [
            re.compile(r"([A-ZÀ-Úa-zà-ú\s]+?)\s*\(INVESTIGADO\)", re.IGNORECASE),
            re.compile(r"([A-ZÀ-Úa-zà-ú\s]+?)\s*\(FLAGRANTEADO\)", re.IGNORECASE),
            re.compile(r"AUTOR\(A\)\s*\(ES\)\s*:\s*([A-ZÀ-Úa-zà-ú\s]+?)\s*", re.IGNORECASE),
            re.compile(r"([A-ZÀ-Úa-zà-ú\s]+?)\s*\(REU\)", re.IGNORECASE),
            re.compile(r"contra\s+([A-ZÀ-Úa-zà-ú\s]+?)\s*,\s*brasileiro", re.IGNORECASE),
            re.compile(r"DENÚNCIA\s*,\s*com\s+base\s+no\s+Inquérito\s+Policial\s+anexo,\s+contra\s*:\s*([A-ZÀ-Úa-zà-ú\s]+?)\s*,\s*brasileiro", re.IGNORECASE),
            re.compile(r"([A-ZÀ-Úa-zà-ú\s]+?)\s*\(REQUERIDO\)", re.IGNORECASE),
            re.compile(r"([A-ZÀ-Úa-zà-ú\s]+?)\s*\(RÉU|ACUSADO|DENUNCIADO\)", re.IGNORECASE),
            re.compile(r"Réu:\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\(|\n|,|\Z)", re.IGNORECASE),
            re.compile(r"Réu:\s*\n\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\n|,|\Z)", re.IGNORECASE),
            re.compile(r"Réu:\s*\n\s*\n\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\n|,|\Z)", re.IGNORECASE),
            re.compile(r"Réu:\s*([A-ZÀ-Úa-zà-ú\s]+?)\s*\n", re.IGNORECASE),
            re.compile(r"Réu:\s*\n\s*([A-ZÀ-Úa-zà-ú\s]+?)\s*\n", re.IGNORECASE),
            re.compile(r"\b(CARLOS HELIO DE SOUZA SILVA|LUIZ ALBERTO FERNANDES DE SOUZA|DIEGO DOS SANTOS)\b", re.IGNORECASE)
        ]
        
        for pattern in patterns_assisted_name_primary:
            match = pattern.search(text)
            if match:
                name_candidate = match.group(1).strip() if match.group(1) else None
                assisted_name = process_assisted_name(name_candidate)
                if assisted_name:
                    break

        # Lógica de Fallback: Se o nome do assistido ainda não foi encontrado ou se foi identificado como "Autoridade"
        if assisted_name is None or "Autoridade" in assisted_name:
            logging.info("Tentando extração de fallback para o nome do assistido.")
            patterns_assisted_name_fallback = [
                re.compile(r"AGRESSOR\(A\)\s*INVESTIGADO\(A\):\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\n|,|\Z)", re.IGNORECASE),
                re.compile(r"INVESTIGADO\(A\):\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\n|,|\Z)", re.IGNORECASE),
                re.compile(r"RÉU:\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\n|,|\Z)", re.IGNORECASE),
                re.compile(r"ACUSADO:\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\n|,|\Z)", re.IGNORECASE),
                re.compile(r"REQUERIDO:\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\n|,|\Z)", re.IGNORECASE),
            ]
            
            for pattern in patterns_assisted_name_fallback:
                match = pattern.search(text)
                if match:
                    name_candidate = match.group(1).strip() if match.group(1) else None
                    assisted_name = process_assisted_name(name_candidate)
                    if assisted_name:
                        break
        
        # Extração do Órgão Julgador
        pattern_court = re.compile(r"Órgão julgador:\s*(.+?)(?:\n|\Z)", re.IGNORECASE)
        match_court = pattern_court.search(text)
        if match_court:
            court_name = match_court.group(1).strip() if match_court.group(1) else None
        
        if court_name is not None:
            court_name = court_name.strip()

        return assisted_name, court_name
    except Exception as e:
        logging.error(f"Erro ao extrair informações do PDF {pdf_path}: {e}")
        return None, None

# --- Gerenciamento de pastas no Google Drive --- #
def get_or_create_folder(drive_service, folder_name, parent_folder_id):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed = false"
    response = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = response.get('files', [])

    if folders:
        return folders[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata, fields='id').execute()
        logging.info(f"Pasta '{folder_name}' criada com ID: {folder.get('id')}")
        return folder.get('id')

# --- Processamento principal --- #
def main():
    drive_service = authenticate_google_drive()
    
    query = f"'{SOURCE_FOLDER_ID}' in parents and mimeType = 'application/pdf' and trashed = false"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])

    if not items:
        logging.info("Nenhum arquivo PDF encontrado na pasta de origem.")
        return

    logging.info(f"Encontrados {len(items)} arquivos PDF na pasta de origem.")

    for item in items:
        file_id = item['id']
        file_name = item['name']
        logging.info(f"Processando arquivo: {file_name} (ID: {file_id})")

        request = drive_service.files().get_media(fileId=file_id)
        pdf_content = request.execute()
        temp_pdf_path = f"/tmp/{file_name}"
        with open(temp_pdf_path, 'wb') as f:
            f.write(pdf_content)

        assisted_name, court_name = extract_info_from_pdf(temp_pdf_path)
        os.remove(temp_pdf_path)

        if assisted_name and court_name:
            logging.info(f"Nome do assistido encontrado: {assisted_name}, Órgão Julgador: {court_name}")
            
            # Determina o nome da pasta da vara no Drive
            court_drive_folder_name = COURT_FOLDER_MAPPING.get(court_name.upper(), None)

            if court_drive_folder_name:
                if isinstance(court_drive_folder_name, str) and court_drive_folder_name.startswith('1_') and len(court_drive_folder_name) == 33:
                    # Se o mapeamento for um ID de pasta direto, usa-o como pai.
                    parent_folder_for_assisted = court_drive_folder_name
                elif court_drive_folder_name == "Processos - VVD":
                    # Se for a pasta principal de VVD, usa o ROOT_DESTINATION_FOLDER_ID.
                    parent_folder_for_assisted = ROOT_DESTINATION_FOLDER_ID
                else:
                    # Para outros casos, cria uma subpasta para a vara dentro do ROOT_DESTINATION_FOLDER_ID.
                    parent_folder_for_assisted = get_or_create_folder(drive_service, court_drive_folder_name, ROOT_DESTINATION_FOLDER_ID)
            else:
                # Lógica para órgãos julgadores não mapeados: criar pasta dinâmica por comarca
                comarca_match = re.search(r"(?:DA COMARCA DE|DE)\s*([A-ZÀ-Úa-zà-ú\s]+?)(?:\s*\Z|\s*\n)", court_name, re.IGNORECASE)
                if comarca_match:
                    comarca_name = comarca_match.group(1).strip().title()
                    dynamic_court_folder_name = f"Processos - {comarca_name}"
                    parent_folder_for_assisted = get_or_create_folder(drive_service, dynamic_court_folder_name, DYNAMIC_COURT_ROOT_FOLDER_ID)
                else:
                    logging.warning(f"Não foi possível determinar a comarca para o órgão julgador \'{court_name}\'. Arquivo \'{file_name}\' não movido.")
                    continue # Pula para o próximo arquivo
                
            logging.info(f"ROOT_DESTINATION_FOLDER_ID: {ROOT_DESTINATION_FOLDER_ID}")
            logging.info(f"DYNAMIC_COURT_ROOT_FOLDER_ID: {DYNAMIC_COURT_ROOT_FOLDER_ID}")
            logging.info(f"parent_folder_for_assisted (ID ou nome): {parent_folder_for_assisted}")

            # Cria ou obtém a pasta do assistido dentro da pasta pai determinada
            assisted_folder_id = get_or_create_folder(drive_service, assisted_name, parent_folder_for_assisted)
            logging.info(f"Pasta do assistido \'{assisted_name}\' ID: {assisted_folder_id}")

            # Copia o arquivo para a pasta de destino
            copied_file_metadata = {
                'name': file_name,
                'parents': [assisted_folder_id]
            }
            copied_file_response = drive_service.files().copy(
                fileId=file_id, body=copied_file_metadata).execute()
            copied_file_id = copied_file_response.get('id')
            logging.info(f"Arquivo \'{file_name}\' (ID: {file_id}) copiado para a pasta \'{assisted_name}\' (ID: {assisted_folder_id}) com novo ID: {copied_file_id}.")

            # Exclui o arquivo original da pasta de origem
            drive_service.files().delete(fileId=file_id).execute()
            logging.info(f"Arquivo original \'{file_name}\' (ID: {file_id}) excluído da pasta de origem.")

            # VERIFICAÇÃO: Listar conteúdo da pasta do assistido para confirmar a presença do arquivo
            query_check = f"'{assisted_folder_id}' in parents and name = '{file_name}' and trashed = false"
            check_response = drive_service.files().list(q=query_check, spaces='drive', fields='files(id, name)').execute()
            found_files = check_response.get('files', [])

            if found_files:
                logging.info(f"VERIFICAÇÃO: Arquivo \'{file_name}\' encontrado na pasta \'{assisted_name}\' (ID: {assisted_folder_id}) após a cópia.")
            else:
                logging.error(f"VERIFICAÇÃO: Arquivo \'{file_name}\' NÃO encontrado na pasta \'{assisted_name}\' (ID: {assisted_folder_id}) após a cópia. Possível problema de sincronização ou API.")
        else:
            logging.warning(f"Órgão julgador '{court_name}' não mapeado para uma pasta específica. Arquivo '{file_name}' não movido.")
    else:
        logging.error(f"Não foi possível extrair nome do assistido ou órgão julgador do arquivo \'{file_name}\' . Arquivo não movido.")

if __name__ == '__main__':
    main()

