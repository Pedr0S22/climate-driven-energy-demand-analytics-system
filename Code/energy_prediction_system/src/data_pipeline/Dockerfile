FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos (contexto de build: energy_prediction_system/)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a pasta src para /app/src
COPY src/ /app/src/

# Corrige finais de linha (CRLF -> LF) para compatibilidade com Linux
RUN apt-get update && apt-get install -y sed && sed -i 's/\r$//' /app/src/data_pipeline/run_pipeline.sh

# Define o PYTHONPATH para a nova localização
ENV PYTHONPATH=/app/src

# Dá permissões de execução ao script
RUN chmod +x /app/src/data_pipeline/run_pipeline.sh

# Trigger real-time pipeline directly
CMD ["python", "/app/src/data_pipeline/real_time_pipeline.py"]
