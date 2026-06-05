# Imagem para deploy na nuvem (Render, Fly.io, etc.)
FROM python:3.12-slim

WORKDIR /app

# Bibliotecas para Pillow e compilacao pontual de dependencias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY api/ ./api/
COPY src/ ./src/
COPY modelo-ui/ ./modelo-ui/

RUN mkdir -p /app/dados /app/log

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Render injeta PORT em tempo de execucao
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
