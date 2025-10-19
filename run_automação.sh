#!/bin/bash
LOG_FILE="/home/ubuntu/automação_distribuição_pdfs.log"

echo "$(date): Iniciando execução do script de automação." >> $LOG_FILE 2>&1
cd /home/ubuntu >> $LOG_FILE 2>&1
python3 /home/ubuntu/automação_distribuição_pdfs.py >> $LOG_FILE 2>&1
echo "$(date): Execução do script de automação finalizada." >> $LOG_FILE 2>&1

