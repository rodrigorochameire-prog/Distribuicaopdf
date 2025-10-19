FROM python:3.11-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webhook_server.py .
COPY automação_distribuição_pdfs.py .
COPY credentials.json .
COPY token.json .

ENV PORT 8080
EXPOSE 8080

CMD ["python", "webhook_server.py"]

