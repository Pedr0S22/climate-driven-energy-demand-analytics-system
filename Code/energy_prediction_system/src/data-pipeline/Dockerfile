# Imagem base ligeiramente mais robusta para cálculos matemáticos
FROM python:3.11-slim

WORKDIR /app

# Dependências para processamento de dados e compiladores C
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instalar bibliotecas de Data Science (ex: pandas==2.1.0, scikit-learn==1.3.1)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O Pipeline não expõe portas, ele comunica via rede interna com a DB
# Comando que executa o fluxo completo do pipeline
CMD ["python", "run_pipeline.py"]