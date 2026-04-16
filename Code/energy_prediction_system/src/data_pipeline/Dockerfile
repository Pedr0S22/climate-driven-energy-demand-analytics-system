FROM python:3.11-slim

WORKDIR /

# Instala dependências do sistema
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copia os requirements da raiz do projeto para o contentor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a tua pasta src local para a pasta /src no contentor
COPY src/ /src/

# Define o PYTHONPATH para a nova localização
ENV PYTHONPATH=/src

# Dá permissões de execução ao script na nova localização
RUN chmod +x /src/data_pipeline/run_pipeline.sh

# Comando para arrancar
CMD ["/src/data_pipeline/run_pipeline.sh"]