# Utilizar imagem slim para reduzir a superfície de ataque e tamanho
FROM python:3.11-slim

# Definir o diretório de trabalho conforme a convenção
WORKDIR /app

# Instalar dependências de sistema para saúde (healthcheck) e drivers DB
RUN apt-get update && apt-get install -y \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas os requisitos primeiro para otimizar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código fonte da API
COPY . .

# Expor a porta do serviço
EXPOSE 8000

# Comando de inicialização (ajusta para o teu entrypoint real)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]