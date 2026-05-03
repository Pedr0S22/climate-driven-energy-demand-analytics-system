FROM python:3.11-slim

# Definir o diretório de trabalho
WORKDIR /app

# Instalar dependências de sistema necessárias para o PyQt6 e interface gráfica no Linux
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libfontconfig1 \
    libx11-6 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-randr0 \
    libxcb-render0 \
    libxcb-util1 \
    libxcb-xfixes0 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar os requisitos primeiro
COPY requirements.txt .

# Instala as dependências (mesmo que o ficheiro esteja vazio, o comando não falha)
RUN pip install --no-cache-dir -r requirements.txt || true

# Copiar o resto do código da aplicação
COPY . .

# Definir a variável de ambiente para o display (necessário para X11 Forwarding)
ENV DISPLAY=:0

# Comando para iniciar a aplicação
CMD ["python", "src/app/main.py"]
