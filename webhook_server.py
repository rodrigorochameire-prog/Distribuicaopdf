import os
from flask import Flask, request, jsonify
import subprocess
import logging

app = Flask(__name__)

# --- Configuração de Logging para o Webhook Server ---
WEBHOOK_LOG_FILE = "webhook_server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(WEBHOOK_LOG_FILE),
        logging.StreamHandler()
    ]
)

# Caminho para o script de automação principal
AUTOMATION_SCRIPT_PATH = "/home/ubuntu/automação_distribuição_pdfs.py"

@app.route('/webhook', methods=['POST'])
def webhook():
    logging.info(f"Webhook recebido! Método: {request.method}")
    
    # Google Drive Webhook notifications are typically empty POST requests
    # with relevant information in headers or just a trigger.
    # We'll check for a specific header to confirm it's a Google Drive notification
    # and then trigger the automation script.
    
    # Check for Google Drive specific header (e.g., X-Goog-Channel-ID, X-Goog-Resource-State)
    # For simplicity, we'll just check if it's a POST and then trigger.
    # A more robust solution would validate the channel ID and resource state.

    if request.method == 'POST':
        logging.info("Requisição POST recebida. Disparando automação...")
        try:
            # Executa o script de automação em um processo separado
            # Isso evita que o webhook server fique bloqueado esperando a automação terminar
            subprocess.Popen(["python3", AUTOMATION_SCRIPT_PATH])
            logging.info("Script de automação disparado com sucesso.")
            return jsonify({'status': 'Automation triggered'}), 200
        except Exception as e:
            logging.error(f"Erro ao disparar o script de automação: {e}")
            return jsonify({'status': 'Error triggering automation', 'error': str(e)}), 500
    
    logging.warning("Requisição não POST recebida no webhook.")
    return jsonify({'status': 'Method Not Allowed'}), 405

@app.route('/')
def index():
    return "Webhook server is running. Send POST requests to /webhook"

if __name__ == '__main__':
    # O Flask roda na porta 5000 por padrão. Precisamos expor essa porta.
    # debug=True é útil para desenvolvimento, mas deve ser False em produção.
    app.run(host='0.0.0.0', port=5000, debug=False)

