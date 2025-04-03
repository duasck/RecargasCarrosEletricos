FROM python:3.9-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código fonte
COPY ./src /app

# Configurações do Python
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "--version"]